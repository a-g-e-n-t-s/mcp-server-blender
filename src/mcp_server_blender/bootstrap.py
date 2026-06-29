# ----------------------------------------------------------------------------------------------------
# bootstrap.py
# ----------------------------------------------------------------------------------------------------

"""
Bootstrap script — runs inside headless Blender.

Started via: blender --background --python bootstrap.py
Sets up a TCP socket server that receives JSON commands and executes bpy operations.
Same socket protocol as the blender-mcp addon but without the UI panel.
"""

# ----------------------------------------------------------------------------------------------------
import bpy
import json
import os
import queue
import socket
import sys
import threading
import traceback

SOCKET_HOST = os.getenv("BLENDER_SOCKET_HOST", "127.0.0.1")
SOCKET_PORT = int(os.getenv("BLENDER_SOCKET_PORT", "9876"))

# Main-thread command queue: socket threads put (command, response_queue) tuples here.
# The main thread pops and executes them so bpy.ops calls don't deadlock.
_command_queue = queue.Queue()

# ----------------------------------------------------------------------------------------------------
class BlenderSocketServer:
    def __init__(self, host=SOCKET_HOST, port=SOCKET_PORT):
        self.host = host
        self.port = port
        self.running = False
        self.sock = None
        self.thread = None

    def start(self):
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(1.0)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        self.thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.thread.start()
        print(f"[bootstrap] Socket server listening on {self.host}:{self.port}")

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()
            self.sock = None

    def _accept_loop(self):
        while self.running:
            try:
                client, addr = self.sock.accept()
                print(f"[bootstrap] Client connected: {addr}")
                t = threading.Thread(target=self._handle_client, args=(client,), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except OSError:
                break

    def _handle_client(self, client):
        client.settimeout(180.0)
        buf = b""
        try:
            while self.running:
                data = client.recv(8192)
                if not data:
                    break
                buf += data
                try:
                    command = json.loads(buf.decode("utf-8"))
                    buf = b""
                    cmd_name = command.get("command", "?")
                    print(f"[bootstrap] Queuing command: {cmd_name}")

                    # Put command on main-thread queue and wait for result
                    result_queue = queue.Queue()
                    _command_queue.put((command, result_queue))
                    response = result_queue.get(timeout=120.0)

                    response_bytes = json.dumps(response).encode("utf-8")
                    print(f"[bootstrap] Sending response ({len(response_bytes)} bytes)")
                    client.sendall(response_bytes)
                except json.JSONDecodeError:
                    continue
                except queue.Empty:
                    client.sendall(json.dumps({"success": False, "error": "Command timed out waiting for main thread"}).encode("utf-8"))
        except Exception as e:
            print(f"[bootstrap] Client error: {e}")
            traceback.print_exc()
        finally:
            client.close()

    def execute_command(self, command):
        cmd = command.get("command", "")
        params = command.get("params", {})
        try:
            if cmd == "heartbeat":
                return {"success": True, "status": "alive", "version": bpy.app.version_string}
            elif cmd == "create_object":
                return self._create_object(params)
            elif cmd == "modify_object":
                return self._modify_object(params)
            elif cmd == "set_material":
                return self._set_material(params)
            elif cmd == "render":
                return self._render(params)
            elif cmd == "export":
                return self._export(params)
            elif cmd == "execute_python":
                return self._execute_python(params)
            elif cmd == "get_scene_info":
                return self._get_scene_info(params)
            else:
                return {"success": False, "error": f"Unknown command: {cmd}"}
        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    # ========================================================================
    # Command Implementations
    # ========================================================================

    @staticmethod
    def _tag_redraw():
        """Force viewport redraw — needed when commands run from timer callbacks."""
        try:
            for area in bpy.context.screen.areas if bpy.context.screen else []:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
            bpy.context.view_layer.update()
        except Exception:
            pass

    def _create_object(self, p):
        obj_type = p.get("type", "cube").lower()
        loc = tuple(p.get("location", [0, 0, 0]))
        scl = tuple(p.get("scale", [1, 1, 1]))
        rot = tuple(r * 3.14159265 / 180 for r in p.get("rotation", [0, 0, 0]))

        ops = {
            "cube": bpy.ops.mesh.primitive_cube_add,
            "sphere": bpy.ops.mesh.primitive_uv_sphere_add,
            "cylinder": bpy.ops.mesh.primitive_cylinder_add,
            "plane": bpy.ops.mesh.primitive_plane_add,
            "cone": bpy.ops.mesh.primitive_cone_add,
            "torus": bpy.ops.mesh.primitive_torus_add,
        }
        op = ops.get(obj_type)
        if not op:
            return {"success": False, "error": f"Unknown type: {obj_type}. Supported: {', '.join(ops.keys())}"}

        # Use temp_override for Blender 4.x to provide valid context in timer callbacks
        if hasattr(bpy.context, "temp_override"):
            window = bpy.context.window_manager.windows[0]
            screen = window.screen
            area = next((a for a in screen.areas if a.type == 'VIEW_3D'), screen.areas[0])
            region = next((r for r in area.regions if r.type == 'WINDOW'), area.regions[0])
            with bpy.context.temp_override(window=window, area=area, region=region):
                op(location=loc, rotation=rot)
        else:
            op(location=loc, rotation=rot)

        obj = bpy.context.active_object
        if obj:
            obj.scale = scl
            name = p.get("name")
            if name:
                obj.name = name
            self._tag_redraw()
            return {"success": True, "name": obj.name, "type": obj_type}
        else:
            return {"success": False, "error": "Object created but not found in context"}

    def _modify_object(self, p):
        name = p.get("name")
        obj = bpy.data.objects.get(name)
        if not obj:
            return {"success": False, "error": f"Object not found: {name}"}

        if p.get("location"):
            obj.location = tuple(p["location"])
        if p.get("scale"):
            obj.scale = tuple(p["scale"])
        if p.get("rotation"):
            obj.rotation_euler = tuple(r * 3.14159265 / 180 for r in p["rotation"])

        modifier = p.get("modifier")
        if modifier:
            mod = obj.modifiers.new(name=modifier, type=modifier.upper())
            mp = p.get("modifier_params", {})
            for k, v in mp.items():
                if hasattr(mod, k):
                    setattr(mod, k, v)

        self._tag_redraw()
        return {"success": True, "name": obj.name}

    def _set_material(self, p):
        obj_name = p.get("object_name")
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            return {"success": False, "error": f"Object not found: {obj_name}"}

        mat_name = p.get("material_name") or f"{obj_name}_material"
        mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            color = p.get("color", [0.8, 0.8, 0.8, 1.0])
            bsdf.inputs["Base Color"].default_value = tuple(color)
            bsdf.inputs["Roughness"].default_value = p.get("roughness", 0.5)
            bsdf.inputs["Metallic"].default_value = p.get("metallic", 0.0)

        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

        self._tag_redraw()
        return {"success": True, "material": mat_name, "object": obj_name}

    def _render(self, p):
        import tempfile
        output = p.get("output_path") or os.path.join(tempfile.gettempdir(), "blender-renders", "render.png")
        os.makedirs(os.path.dirname(output), exist_ok=True)

        scene = bpy.context.scene
        scene.render.resolution_x = p.get("resolution_x", 1920)
        scene.render.resolution_y = p.get("resolution_y", 1080)
        scene.render.filepath = output
        scene.render.image_settings.file_format = "PNG"

        engine = p.get("engine", "CYCLES").upper()

        # EEVEE requires GPU/OpenGL — auto-fallback to CYCLES in headless mode
        eevee_names = ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "EEVEE")
        if engine in eevee_names:
            print(f"[bootstrap] Warning: {engine} requires GPU, falling back to CYCLES (CPU)")
            engine = "CYCLES"

        scene.render.engine = engine
        if engine == "CYCLES":
            scene.cycles.samples = p.get("samples", 32)
            scene.cycles.device = "CPU"
            scene.cycles.use_denoising = False

        bpy.ops.render.render(write_still=True)
        size = os.path.getsize(output) if os.path.exists(output) else 0
        return {"success": True, "output_path": output, "size_bytes": size, "engine": engine}

    def _export(self, p):
        fmt = p.get("format", "gltf").lower()
        output = p.get("output_path")
        selected = p.get("selected_only", False)

        ext_map = {"gltf": ".glb", "glb": ".glb", "fbx": ".fbx", "obj": ".obj", "stl": ".stl"}
        ext = ext_map.get(fmt)
        if not ext:
            return {"success": False, "error": f"Unknown format: {fmt}. Supported: {', '.join(ext_map.keys())}"}

        if not output:
            import tempfile
            output = os.path.join(tempfile.gettempdir(), "blender-exports", f"export{ext}")
        os.makedirs(os.path.dirname(output), exist_ok=True)

        try:
            if fmt in ("gltf", "glb"):
                bpy.ops.export_scene.gltf(filepath=output, use_selection=selected)
            elif fmt == "fbx":
                bpy.ops.export_scene.fbx(filepath=output, use_selection=selected)
            elif fmt == "obj":
                bpy.ops.wm.obj_export(filepath=output, export_selected_objects=selected)
            elif fmt == "stl":
                # bpy.ops.export_mesh.stl removed in Blender 4.x — use wm.stl_export
                if hasattr(bpy.ops.wm, "stl_export"):
                    bpy.ops.wm.stl_export(filepath=output, export_selected_objects=selected)
                elif hasattr(bpy.ops.export_mesh, "stl"):
                    bpy.ops.export_mesh.stl(filepath=output, use_selection=selected)
                else:
                    return {"success": False, "error": "STL export not available in this Blender version"}
        except Exception as e:
            return {"success": False, "error": f"Export failed: {e}"}

        size = os.path.getsize(output) if os.path.exists(output) else 0
        return {"success": True, "output_path": output, "format": fmt, "size_bytes": size}

    def _execute_python(self, p):
        code = p.get("code", "")
        local_vars = {}
        import io
        captured = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = captured
            exec(code, {"bpy": bpy, "__builtins__": __builtins__}, local_vars)
            sys.stdout = old_stdout
            result = local_vars.get("result", None)
            stdout_output = captured.getvalue()
            if result is not None:
                return {"success": True, "result": str(result), "stdout": stdout_output}
            elif stdout_output:
                return {"success": True, "result": stdout_output}
            else:
                return {"success": True, "result": None}
        except Exception as e:
            sys.stdout = old_stdout
            return {"success": False, "error": str(e), "stdout": captured.getvalue()}

    def _get_scene_info(self, p):
        objects = []
        for obj in bpy.data.objects:
            o = {
                "name": obj.name,
                "type": obj.type,
                "location": list(obj.location),
                "rotation": [r * 180 / 3.14159265 for r in obj.rotation_euler],
                "scale": list(obj.scale),
                "visible": obj.visible_get(),
            }
            if obj.data and hasattr(obj.data, "materials"):
                o["materials"] = [m.name for m in obj.data.materials if m]
            objects.append(o)

        return {
            "success": True,
            "object_count": len(objects),
            "objects": objects,
            "scene_name": bpy.context.scene.name,
        }


# ============================================================================
# Start server when script is loaded by Blender
# ============================================================================

server = BlenderSocketServer()
server.start()


def _process_command_queue():
    """Drain the command queue on the main thread (one command per tick)."""
    try:
        command, result_queue = _command_queue.get_nowait()
        cmd_name = command.get("command", "?")
        print(f"[bootstrap] Main thread executing: {cmd_name}")
        try:
            response = server.execute_command(command)
        except Exception as e:
            traceback.print_exc()
            response = {"success": False, "error": str(e)}
        result_queue.put(response)
    except queue.Empty:
        pass
    except Exception as e:
        print(f"[bootstrap] Timer error: {e}")
        traceback.print_exc()
    return 0.05  # re-run every 50ms


if bpy.app.background:
    # Headless mode — block the main thread (no event loop to hook into)
    print("[bootstrap] Blender headless mode — processing commands on main thread...")
    try:
        while server.running:
            try:
                command, result_queue = _command_queue.get(timeout=0.5)
                cmd_name = command.get("command", "?")
                print(f"[bootstrap] Main thread executing: {cmd_name}")
                response = server.execute_command(command)
                result_queue.put(response)
            except queue.Empty:
                continue
    except KeyboardInterrupt:
        print("[bootstrap] Shutting down...")
        server.stop()
else:
    # GUI mode — use timer so Blender's event loop stays responsive
    if bpy.app.timers.is_registered(_process_command_queue):
        bpy.app.timers.unregister(_process_command_queue)
    bpy.app.timers.register(_process_command_queue, first_interval=0.1, persistent=True)
    print(f"[bootstrap] GUI mode — socket server on {SOCKET_HOST}:{SOCKET_PORT}, processing via timer")
    print(f"[bootstrap] Timer registered: {bpy.app.timers.is_registered(_process_command_queue)}")
