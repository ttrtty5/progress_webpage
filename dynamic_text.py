bl_info = {
    "name": "dynamic text动态文本",
    "author": "ttrtty5",
    "version": (0, 1, 0),
    "blender": (2, 92, 0),
    "location": "View3D > text > text",
    "warning": "",
    "description": "对text物体的文本k帧",
    "wiki_url": "",
    "tracker_url": "",
    "warning":"卸载后文本动画将不支持, 及可能拖慢预览播放速度",
    "category": "3D View"
}
import bpy
from bpy.app.handlers import persistent, frame_change_pre
from bpy.types import PropertyGroup


# 关于为什么text物体无法动画,因为text物体用的是curve数据, 太离谱了

def softed_frameStart(index,dynamictext):
    if dynamictext[index].frameStart == dynamictext[index-1].frameStart:
        return
    
    if len(dynamictext)==1:
        return
        
    if dynamictext[index].frameStart < dynamictext[index-1].frameStart:
        if index == 0:
            return
        dynamictext.move(index,index-1)
        return softed_frameStart(index-1,dynamictext)
    
    if len(dynamictext)==index+1:
        return
    if dynamictext[index].frameStart > dynamictext[index+1].frameStart:
        dynamictext.move(index,index+1)
        return softed_frameStart(index+1,dynamictext)


def frameStart_update(self,context):
    index = int("".join(list(filter(str.isdigit,self.path_from_id())))) 
    softed_frameStart(index, context.object.data.dynamictext)
    # updateTexts(context.scene)

    
def body_update(self,context):
    index = int("".join(list(filter(str.isdigit,self.path_from_id()))))+1
    if context.scene.frame_current >= self.frameStart:
        if len(context.object.data.dynamictext)==index:
            context.object.data.body = self.body
            return 
        if context.scene.frame_current < context.object.data.dynamictext[index].frameStart:
            context.object.data.body = self.body
    
@persistent
def updateTexts(scene):
    current = scene.frame_current
    if "动画文本" not in bpy.data.collections:
        return
    # print(scene.text_anim.text_list[:])
    for obj in bpy.data.collections["动画文本"].objects:
        if obj.type != 'FONT':
            continue
        dynamictext = obj.data.dynamictext
        length1 = len(dynamictext)-1
        for index,keyframe in enumerate(dynamictext):
            # print(index)
            if current >= keyframe.frameStart:
                if index == length1:
                    obj.data.body = dynamictext[index].body
                    break
                if dynamictext[index+1].frameStart > current:
                    obj.data.body = dynamictext[index].body
                    break
    


# 在curve数据上的动画关键帧属性
class text_object_coll(bpy.types.PropertyGroup):
    frameStart : bpy.props.IntProperty(default=1,description="请勿拖动,请左右按钮或输入数值", min=1, update=frameStart_update)
    body : bpy.props.StringProperty(default="", update=body_update)


# bpy.context.preferences.addons["dynamic_text"].preferences.font_path
class TextPreferences(bpy.types.AddonPreferences):
    bl_idname = "dynamic_text"
    
    font_path: bpy.props.StringProperty(
            name="字体路径:",
            description="生成文本后加载的字体",
            subtype = 'FILE_PATH',
            default = r'C:\WINDOWS\Fonts\Alibaba-PuHuiTi-Regular.ttf'
            )

    def draw(self, context):
        obj = context.object
        layout = self.layout
        row = layout.row()
        row.prop(self, "font_path")

# 操作符
class AddTextFrame(bpy.types.Operator):
    bl_idname = "mi2bl.add_text_frame"
    bl_label = "添加关键帧"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bpy.context.object.type == "FONT"

    def execute(self, context):
        if context.object not in context.scene.text_anim.text_list:
            context.scene.text_anim.text_list.append(context.object)
        dynamictext = context.object.data.dynamictext
        new_frame = dynamictext.add()
        new_frame.body = context.object.data.body
        new_frame.frameStart = context.scene.frame_current
        
        
        # 排序
        '''
        new_index = len(context.object.data.dynamictext)-1
        if new_index < 1: # 有两个的时候才开始排序
            return {'FINISHED'}
        sort_num = 0
        for keyframe in dynamictext:
            if keyframe.frameStart > new_frame.frameStart:
                sort_num+=1
        for x in range(sort_num):
            dynamictext.move(new_index-1,new_index)
            new_index-=1
        '''
        # 突然想到, 直接尾递归排序不就好了
        return {'FINISHED'}

class RemoveTextFrame(bpy.types.Operator):
    bl_idname = "mi2bl.remove_text_frame"
    bl_label = "移除关键帧"
    bl_options = {'UNDO'}

    index : bpy.props.IntProperty()

    @classmethod
    def poll(cls, context):
        return bpy.context.object.type == "FONT"

    def execute(self, context):
        context.object.data.dynamictext.remove(self.index)
        
        if len(context.object.data.dynamictext) == 0:
            context.scene.text_anim.text_list.remove(context.object)
        return {'FINISHED'}

class DYNAMICTEXT_PT_UI(bpy.types.Panel):
    '''3d视图n侧边栏创建区的面板'''
    bl_label = '动态文本'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'text'
    
    def draw(self,context):
        obj = context.object
        layout = self.layout
        row = layout.row()
        row.operator('mi2bl.add_textobject')
        if obj != None:
            if obj.type == 'FONT':
                row = layout.row()
                row.prop(obj.data, 'body')
                row = layout.row()
                row.operator('mi2bl.add_text_frame')
                
                
                # 文本动画部分
                # sorted 排序
                # for index, coll in enumerate(sorted(obj.data.dynamictext, key=lambda t: t.frameStart)):
                for index, coll in enumerate(obj.data.dynamictext):
                    box = layout.box()
                    col = box.column()
                    row = col.row()
                    row.prop(coll, "frameStart", text="起始帧")
                    row.operator("mi2bl.remove_text_frame", text="", icon="X", emboss=False).index = index
                    row = col.row(align=True)
                    sub = row.row()
                    sub.scale_x = 3
                    sub.prop(coll, "body", text="")

        
class 视图文本(bpy.types.Operator):
    bl_idname = 'mi2bl.add_textobject'
    bl_label = '添加视图文本'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.scene.camera == None:
            self.report({'INFO'},"场景内没有相机")
            return {'CANCELLED'}
        
        #生成集合
        if "动画文本" not in context.view_layer.layer_collection.children:
            coll=bpy.data.collections.new("动画文本")
            context.view_layer.layer_collection.collection.children.link(coll)
        else:
            coll=bpy.data.collections["动画文本"]
        
        text_data = bpy.data.curves.new("动画文本","FONT")
        text = bpy.data.objects.new("动画文本", text_data)
        coll.objects.link(text)
        text.parent = context.scene.camera
        text.location.z = -1
        text.scale = (0.1,0.1,0.1)
        text.display.show_shadows = False
        
        if context.preferences.addons["dynamic_text"].preferences.font_path !='':
            font1 = bpy.data.fonts.load(filepath=context.preferences.addons["dynamic_text"].preferences.font_path,check_existing = True)
            text_data.font = font1
            
        return {'FINISHED'}

class text_anim(PropertyGroup):
    text_list = []

classes=(
    视图文本,
    DYNAMICTEXT_PT_UI,
    TextPreferences,
    text_anim,
    text_object_coll,
    AddTextFrame,
    RemoveTextFrame
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    frame_change_pre.append(updateTexts)
    
    
    bpy.types.Scene.text_anim = bpy.props.PointerProperty(type=text_anim)
    bpy.types.Curve.dynamictext = bpy.props.CollectionProperty(type=text_object_coll)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
        
    frame_change_pre.remove(updateTexts)

    del bpy.types.Scene.text_anim
    del bpy.types.Curve.dynamictext


if __name__ == "__main__":
    register()
    #unregister()