import React from 'react';
//const io = require('socket.io-client');
// or with import syntax
//import io from 'socket.io-client';
import {Divider,Input,message,Carousel} from 'antd'
import MyTimeline from './timeline.jsx';

const Search = Input.Search;


export default class Home extends React.Component{
  constructor(props) {
    super(props);
    this.state ={nodeList:[],
                 url:document.domain + ':' + location.port}
  }
  componentDidMount() {
    const port=location.port=='7777' ? 5000 : location.port
    this.socket=pio.connect('http://' + document.domain + ':' + location.port)         
    console.log(document.domain,location.port)
    this.socket.on('connect', function() {
      console.log("youht!!")
      this.emit('my event', {data: 'I\'m connected!'});
        
    });
    this.socket.on('my response',function(json){
       var item1 =document.getElementById("h2")
       
       if (item1){
         item1.innerText=json.x+","+json.y
       }
    });
    this.socket.on('idx',function(json){
       var item2=document.getElementById("h3")
       if (item2){
         item2.innerText=json.idx
       }
    });
    this.socket.on('idx1',function(msg){
       var item3=document.getElementById("h4")
       if (item3) {
        item3.innerText=msg
       }
    });
    this.socket.on('message',function(msg){
       var item4=document.getElementById("h1")
       if (item4) {
        item4.innerText=msg
       }
    });
  }
  handleSearch(value){
    console.log(value)
    $.ajax({
      type: 'GET',    // 请求方式
      url: "http://"+value+"/node/list",    // 另一个服务器 URL
      success: (res, status, jqXHR)=> {
        $("#h1")[0].textContent=value+":"+status
        this.setState({nodeList : res.nodes})
      },
      error: (res,status,error)=>{
        // 控制台查看响应文本，排查错误
        message.error('请输入正确的地址');
      }
    })
//    $.get("http://"+value+"/node/list",(res,status)=>{
//      $("#h1")[0].textContent=value+":"+status
//      this.setState({nodeList : res.nodes})
//    })
  }
   render(){
    const data = this.state.nodeList
    return(
       <div>
         <Divider> carouse </Divider>
         <Carousel effect="fade" autoplay>
          <div ><img src="http://mpic.tiankong.com/db8/b3f/db8b3fa160f9017f61cd6f4af98c83c3/640.jpg@!670w"/></div>
          <div ><img src="http://mpic.tiankong.com/3b0/190/3b01902f75029dcb2320053e59003a8d/640.jpg@!670w"/></div>
          <div><img src="http://mpic.tiankong.com/3a3/f24/3a3f2437ecef7b49aa991fcc82fe2f90/640.jpg@!670w"/></div>
          <div><img src="http://mpic.tiankong.com/c34/81f/c3481f9871f8187fe9af49a2dd5c1abd/640.jpg@!670w"/></div>
        </Carousel>
         <Divider> socket.io </Divider>
         <h1 id="h1"> Hello world </h1>
         <h2 id="h2"> Hello world </h2>
         <h3 id="h3"> Hello world </h3>
         <h4 id="h4"> Hello world </h4>
         <Divider> ajax </Divider>
         <Search
          placeholder="input search text"
          onSearch={(value) => this.handleSearch(value)}
          style={{ width: 200 }} />
         <br/><br/>
         <MyTimeline data={data}/>
       </div>
     )
   }
}
