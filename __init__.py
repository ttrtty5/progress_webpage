bl_info = {
    "name": "progress webpage网页显示渲染进度",
    "author": "ttrtty5",
    "version": (0, 1, 0),
    "blender": (2, 91, 0),
    "location": "图片编辑器-侧边栏-网页-开启服务器",
    "warning": "",
    "description": "网页显示渲染进度",
    "wiki_url": "https://github.com/ttrtty5/progress_webpage",
    "tracker_url": "",
    "warning": "python版本不低于3.7",
    "category": "3D View"
}

from bpy.props import StringProperty, IntProperty, PointerProperty, EnumProperty, BoolProperty, FloatProperty
from bpy.types import PropertyGroup
from bpy.app.handlers import persistent
import time, bpy
from . import pyserver
import threading 
import importlib


#TODO
# 用aiohttp重写服务器模块
# 我也是写完才发现http.server的文档上面写了此库不能用于生成, 坑太多了


class 开启服务器(bpy.types.Operator):
    bl_idname = 'pw.start_server'
    bl_label = '开启服务器'
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return not hasattr(关闭服务器,"server")

    def execute(self, context):
        serverAddress = (context.scene.progress_webpage.ip, context.scene.progress_webpage.port)
        关闭服务器.server = pyserver.HTTPServer(serverAddress, pyserver.RequestHandler)
        
        print(serverAddress[0]+':'+str(serverAddress[1]))
        #serve_Thread(server)
        t1 = threading.Thread(target = pyserver.serve_Thread, args = (关闭服务器.server,))
        t1.daemon = True
        t1.start() 
    
        self.report({'INFO'},"服务器已开启, "+serverAddress[0]+':'+str(serverAddress[1]))
        return {'FINISHED'}

class 关闭服务器(bpy.types.Operator):
    bl_idname = 'pw.close_server'
    bl_label = '关闭服务器'
    bl_options = {'REGISTER', 'UNDO'}
    
    # 借用位置存对象server, 看着没有, 但确实是存在的
    
    @classmethod
    def poll(cls, context):
        return hasattr(cls,"server")
    
    def execute(self, context):
        if hasattr(self,"server"):
            self.server.shutdown()
            # print(self.server)
            delattr(关闭服务器,'server')
            importlib.reload(pyserver)
        
        self.report({'INFO'},"服务器已关闭")
        return {'FINISHED'}


class PW_PT_PANEL(bpy.types.Panel):
    bl_label = "渲染进度网页"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = '网页'
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(context.scene.progress_webpage,'ip')
        row = layout.row()
        row.prop(context.scene.progress_webpage,'port')
        row = layout.row()
        row.operator('pw.start_server')
        row = layout.row()
        row.operator('pw.close_server')



# 添加渲染事件
@persistent
def render_pre_time(scene):
    # 开始计时
    scene.progress_webpage['render_pre_time'] = time.time()

@persistent
def render_post_time(scene):
    # 结束计时
    scene.progress_webpage['render_post_time'] = time.time()
    scene.progress_webpage['Rendering_takes_time'] = round(scene.progress_webpage['render_post_time'] - scene.progress_webpage['render_pre_time'],3)

    #print("当前帧 ", scene.frame_current)
    #print("渲染单帧耗时:",scene.progress_webpage['Rendering_takes_time'])
    

def PW自定义属性卸载():
    name = ['render_pre_time','render_post_time','Rendering_takes_time']
    for scene in bpy.data.scenes:
        for n in name:
            if n in scene.progress_webpage:
                del scene.progress_webpage[n]


# FloatProperty不支持超长浮点数, 过长会自动round(), 所以这里用了自定义属性
class options(PropertyGroup):
    ip: StringProperty(name = 'ip',
    description = '内网ip',
    default = "localhost"
    )
    port: IntProperty(name = "端口",
    min = 1024,
    max = 65535,
    default = 11566
    )
    '''
    render_pre_time: FloatProperty(
        description = '一帧开始时间',
        default = 0.000,
        precision = 3
        )
    render_post_time: FloatProperty(
        description = '一帧结束时间',
        default = 0.000,
        precision = 3
        )'''

classes=(
    开启服务器,
    关闭服务器,
    options,
    PW_PT_PANEL
)

def register(): 
    bpy.app.handlers.render_pre.append(render_pre_time)
    bpy.app.handlers.render_post.append(render_post_time)
    
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.progress_webpage = PointerProperty(type=options)
    # bpy.types.Scene.progress_webpage.name="progress_webpage"

def unregister():
    bpy.app.handlers.render_pre.remove(render_pre_time)
    bpy.app.handlers.render_post.remove(render_post_time)
    
    PW自定义属性卸载()
    
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.progress_webpage
    
    

if __name__ == "__main__":
    register()
    #unregister()