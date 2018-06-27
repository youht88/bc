import React from 'react';
//const io = require('socket.io-client');
// or with import syntax
//import io from 'socket.io-client';
import {Divider,Input,message,Carousel} from 'antd'
import MyTimeline from './timeline.jsx';

const Search = Input.Search;


class BlockList extends React.Component{
  constructor(props) {
    super(props);
  }
  
  render(){
    return(
      <div>
        <Divider orientation="left"><h1>最近的十条交易</h1></Divider>
        <h3> {this.props.maxindex} </h3>
      </div>
    )
  }
}
class TradeForm extends React.Component{
  constructor(props) {
    super(props);
  }
  render(){
    return(
      <Divider orientation="left"><h1>发起新的交易</h1></Divider>
    )
  }
}

class OneSearch extends React.Component{
  constructor(props) {
    super(props);
  }
  render(){
    return(
      <Divider orientation="left"><h1>统一检索</h1></Divider>
    )
  }
}

class GraphForm extends React.Component{
  constructor(props) {
    super(props);
  }
  render(){
    return(
      <Divider orientation="left"><h1>趋势与图表</h1></Divider>
    )
  }
}

export default class Home extends React.Component{
  constructor(props) {
    super(props);
    const port=location.port=='7777'?5000:location.port
    this.state ={url:document.domain + ':' + port}
    this.handleAjax = this.handleAjax.bind(this)
  }
  componentDidMount() {
    this.handleAjax('blockchain/maxindex',
      (value)=>{this.setState({maxindex:value})})
     alert(this.state.maxindex)
    }
  }
  handleAjax(path,cb){
    $.ajax({
      type: 'GET',    // 请求方式
      url: `http://${this.state.url}/${path}`,
      success: (res, status, jqXHR)=> {
        cb(res)
      },
      error: (res,status,error)=>{
        // 控制台查看响应文本，排查错误
        message.error('请输入正确的地址');
      }
    })
  }
   render(){
    const {url,maxindex} = this.state
    return(
       <div>
         <BlockList maxindex={maxindex} url={url}/>
         <TradeForm/>
         <OneSearch/>
         <GraphForm/> 
       </div>
     )
   }
}
