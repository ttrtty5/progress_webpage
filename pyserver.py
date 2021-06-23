from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading 
import time, bpy, os


# Content类型
ContentType={
    "png":"image/png",
    "jpg":"image/jpg",
    "htm":"text/html",
    "html":"text/html",
    "js":"application/x-javascript",
    "gif":"image/gif",
    "css":"text/css"
    }

class RequestHandler(SimpleHTTPRequestHandler):
    # 没了用的页面模板
    Page = '''
    <html>
    <body>
    <table>
    <tr>  <td>工程名:</td>        <td>{filepath}</td></tr>
    <tr>  <td>当前帧</td>         <td>{frame_current}</td></tr>
    <tr>  <td>单帧耗时</td>       <td>{Rendering_takes_time}</td></tr>
    <tr>  <td>进度</td>           <td>{progress}</td></tr>
    <tr>  <td>预计时间</td>       <td>{needtime}</td></tr>
    <tr>  <td>Path</td>           <td>123</td></tr>
    </table>
    </body>
    </html>
    '''

    def do_GET(self):
        print('这次响应'+self.path)
        if "Rendering_takes_time" not in bpy.data.scenes[0].progress_webpage:
            return self.send_content("渲染未开始")
            
        if self.path == "/favicon.ico":
            return self.send_ico()
        
        if self.path !="/":
            if not os.path.exists(os.path.dirname(__file__)+"\\"+self.path[1:]):
                return self.send_404()
            #print(os.path.exists(os.path.dirname(__file__)+"\\"+self.path[1:]))
            return self.send_file()
        
        page = self.create_page()
        self.send_content(page)


    def create_page(self):
        # 这里计算进度
        if bpy.data.filepath=='':
            filepath = "文件未保存"
        else:
            filepath = bpy.data.filepath.split("\\")[-1]
        
        
        Rendering_takes_time = bpy.data.scenes[0].progress_webpage["Rendering_takes_time"]
        frame_allnum = bpy.data.scenes[0].frame_end - bpy.data.scenes[0].frame_start+1
        frame_num = bpy.data.scenes[0].frame_current - bpy.data.scenes[0].frame_start+1
        needtime = Rendering_takes_time*(frame_allnum - frame_num)
        if needtime>60:
            m, s = divmod(needtime, 60)
            h, m = divmod(m, 60)
            needtime = ("%d小时%02d分%02d秒" % (h, m, s))
        else:
            needtime = str(needtime)+"秒"
        
        progress_bar = str(round(frame_num/frame_allnum*100,2))+"%"
        
        progress = str(frame_num)+"/"+str(frame_allnum)
        values = {
            'filepath': filepath,
            'frame_current': bpy.data.scenes[0].frame_current,
            'Rendering_takes_time': Rendering_takes_time,
            'progress': progress,
            'needtime': needtime,
            'progress_bar': progress_bar, 
        }
        #page = self.Page.format(**values)
        with open(os.path.dirname(__file__)+"/index.html","r",encoding='utf-8') as f:
            page = f.read()
            page = page.format(**values)
        return page

    def send_content(self, page):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        #self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page.encode('utf-8'))
        
    def send_file(self):
        #暂时仅图片
        #TODO: 要不要写个访问文件黑名单? 啊, 实在懒得
        self.send_response(200)
        if self.path.split(".")[1] in ContentType:
            self.send_header("Content-type", ContentType[self.path.split(".")[1]])
        else:
            self.send_404()
        self.end_headers()
        
        try:
            with open(os.path.dirname(__file__)+self.path, 'rb') as f:
                self.wfile.write(f.read())
        except Exception as e:
            print(e)
            self.send_404()
    
    def send_ico(self):
        self.send_response(200)
        self.send_header("Content-type", "image/x-icon")
        self.end_headers()
        try:
            with open(os.path.dirname(__file__)+'\\favicon.ico', 'rb') as f:
                self.wfile.write(f.read())
        except Exception as e:
            print(e)
            self.send_404()
            
    def send_404(self):
        self.send_response(404)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        print("404re~")
        self.wfile.write("404".encode('utf-8'))
        
        
        
def serve_Thread(server):
    server.serve_forever()
    print('服务器已经关闭')
    

if __name__ == '__main__':
    serverAddress = ('192.168.1.2', 11566)
    server = HTTPServer(serverAddress, RequestHandler)
    print(serverAddress[0]+':'+str(serverAddress[1]))
    #serve_Thread(server)
    t1 = threading.Thread(target = serve_Thread, args = (server,))
    t1.start() 
    
    #server.shutdown()
  
    


