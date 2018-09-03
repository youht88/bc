import React from 'react';
import moment from 'moment';
import { Row, Col ,message,notification} from 'antd';
import { Card ,Avatar,Icon,Tag} from 'antd';
const { Meta } = Card;
import {Timeline} from 'antd';
import {Link} from 'react-router-dom'
import { Form, Input, Button } from 'antd';
const FormItem = Form.Item;

import MyEcharts from './echarts.jsx';

const port = location.port=='7777' ? 5000 : location.port
const node = document.domain + ':' + port

function handleAjax(peer,path,cb){
  if (!peer)
    return
  $.ajax({
    type: 'GET',    // 请求方式
    url: `http://${peer}/${path}`,
    success: (res, status, jqXHR)=> {
      cb(res)
    },
    error: (res,status,error)=>{
      notification.error(
        {message:"出现错误",
         description:`http://${peer}/${path}错误,请输入正确的地址`
        });
    }
  })
}

class FormNode extends React.Component {
  constructor() {
    super();
    this.handleSubmit = this.handleSubmit.bind(this)
  }
  componentDidMount() {
     
  }
  handleSubmit(e){
    e.preventDefault();
    this.props.form.validateFields((err,values)=>{
      if(err){
        message.error("请输入正确的node.")
        return
      }
      if (this.props.onSubmit){
        this.props.onSubmit(values.node)
      }
    });
        
  }

  render() {
    const { getFieldDecorator} = this.props.form;
    return (
      <div style={{margin:10}}>
        <Form id="form" layout="inline">
          <FormItem
            label="节点"
          >
          {getFieldDecorator('node', {
            initialValue:this.props.node,
            rules: [
              {required: true, message: '请输入node' }],
          })(
             <Input style={{width:400}}placeholder="input node like host:port" />
          )}
          </FormItem>
          <FormItem >
            <Button type="primary" onClick={this.handleSubmit}>检索</Button>
          </FormItem>
        </Form>
      </div>
    );
  }
}
const WrappedForm = Form.create()(FormNode)

class NodeInfo extends React.Component{
  constructor(props){
    super(props)
    this.state={node:this.props.node}
  }
  componentDidMount(){
    this.getData(this.props.node)
  }
  componentWillReceiveProps(nextProps){
    if (this.state.node != nextProps.node){
      this.setState({node:nextProps.node})
      this.getData(nextProps.node)
    }else if(nextProps.info){
      this.setState({info:nextProps.info})
    }
  }
  
  getData(node){
    handleAjax(node,'node/info',
      (value)=>{
        this.setState({info:value})
        this.props.handleSetInfo(value)
      }
    )
  }
  
  render(){
    const {info} = this.state
    if (info){
      return(
        <div style={{margin:10}}>
          <h3><Tag color="red" style={{width:120}}>me</Tag>{info && info.me}</h3>
          <h3><Tag color="red" style={{width:120}}>entryNode</Tag>{info && info.entryNode}</h3>
          <h3><Tag color="red" style={{width:120}}>entryNodes</Tag>{info && String(info.entryNodes)}</h3>
          <h3><Tag color="red" style={{width:120}}>lastblock</Tag>{info && info["blockchain.maxindex"]}-{info && info["blockchain.maxindex.nonce"]}</h3> 
          <h3><Tag color="red" style={{width:120}}>isMining</Tag>{info && info.isMining||"no"}</h3> 
          <h3><Tag color="red" style={{width:120}}>isBlockSyncing</Tag>{info && info.isBlockSyncing||"no"}</h3> 
          <h4><Tag color="red" style={{width:120}}>wallet.address</Tag>{info && info["wallet.address"]}</h4> 
          <h3><Tag color="red" style={{width:120}}>wallet.balance</Tag>{info && info["wallet.balance"]}</h3> 
        </div>
      )
    }else{
      return null
    }
  }
}

class NodeList extends React.Component{
  constructor(props){
    super(props)
    this.state={data:[],links:[]}
    this.handleSetInfo = this.handleSetInfo.bind(this)
  }
  componentDidMount(){
    this.setState({node:this.props.node})
    this.getData(this.props.node)
  }
  componentWillReceiveProps(nextProps){
    if (this.state.node != nextProps.node){
      this.setState({node:nextProps.node})
      this.getData(nextProps.node)
    }
  }
  getData(node){
    handleAjax(node,'node/info',
      (value)=>{
        this.setState({info:value})
        data=value.peers.map(
              (peer)=>{return {name:peer.peer.split(".",1)[0],value:0,symbolSize:60,label:{show:true},itemStyle:{color:"#ff0000"}}}
            )        
        this.setState({data:data})
      }
     )
  }
  handleChange(peer){
    this.setState({data:[],links:[]})
  }
  handleSetInfo(value){
    const link={"source":value.me.split(".",1)[0],"target":value.entryNode.split(".",1)[0]}
    let {links,data} = this.state
    let have=false
    for (let i=0;i<links.length-1;i++){
      if (links[i] === value.me.split(".",1)[0]){
        links[i].target=value.entryNode.split(".",1)[0]
        have=true
        break
      }
    }
    if (!have){
      links.push(link)
    }
    for (let i=0;i<data.length -1 ;i++){
      if (data[i].name === value.me.split(".",1)[0]){
        if (data[i].name === value.entryNode.split(".",1)[0]){
          data[i].symbolSize = 60
          data[i].itemStyle.color="#ff0000"
        }else{
          switch (value.entryNodes.length){
            case 0:
              data[i].symbolSize = 60 
              data[i].itemStyle.color="#0000f0"
              break
            case 1:
              data[i].symbolSize = 50
              data[i].itemStyle.color="#d00000"
              break
            case 2:
              data[i].symbolSize = 40
              data[i].itemStyle.color="#b00000"
              break
            case 3:
              data[i].symbolSize = 30
              data[i].itemStyle.color="#900000"
              break
          }
        }
      }
    }
    this.setState({data:data})
    this.setState({links:links})
  }
  render(){
    const {info,data,links} = this.state
    return(
      <div style={{margin:10}}>
        <NodeInfo info={info}/>
        <Timeline>
          {info && info.peers.map((peer)=>
             <Timeline.Item color={(peer.isAlive)?"green":"red"}>
               <Tag color="blue" onClick={()=>this.handleChange(peer.peer)}>{peer.peer}</Tag>
                <NodeInfo node={peer.peer} handleSetInfo={this.handleSetInfo}/>
             </Timeline.Item>
           )
          }
        </Timeline>
        <MyEcharts type="graph" title="网络节点" data={data} links={links} size={{width:600,height:400}}/>
      </div> 
    )
  }
}
/*const data=[
        {name: "120",value:100,symbolSize:40,label:{show:true}},
        {name: "zw0",value:200,symbolSize:40,label:{show:true}},
        {name: "zw1",value:800,symbolSize:40,label:{show:true}},
        {name: "3b0",value:800,symbolSize:40,label:{show:true}},
        {name: "3b1",value:800,symbolSize:40,label:{show:true}},
        {name: "imac",value:800,symbolSize:40,label:{show:true}}
      ]
*/
let data=[]
const links=[
        {source:'zw0_bc',target:'120'},
        {source:'zw1_bc',target:'zw0_bc'},
        {source:'3b0_bc',target:'120'},
        {source:'3b1_bc',target:'3b0_bc'},
        {source:'imac_bc',target:'zw0_bc'},
      ]

export default class Node extends React.Component{
  constructor(props) {
    super(props);
    this.state={}
    this.onSubmit = this.onSubmit.bind(this)
  }
  componentWillMount(){
    this.setState({node})
  }
  onSubmit(node){
    this.setState({node})
  }
  render(){
    const {info,node} = this.state
    return(
     <div>
      <WrappedForm onSubmit={this.onSubmit.bind(this)}/>
      <NodeList node={node}/>
    </div>
    )
  }
}
