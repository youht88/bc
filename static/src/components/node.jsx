import React from 'react';
import moment from 'moment';
import { Row, Col ,message,notification} from 'antd';
import { Card ,Avatar,Icon,Tag} from 'antd';
const { Meta } = Card;
import {Timeline} from 'antd';
import {Link} from 'react-router-dom'
import { Form, Input, Button } from 'antd';
const FormItem = Form.Item;

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
    this.state={}
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
      }
     )
  }
  handleChange(peer){
    this.setState({})
  }
  render(){
    const {info} = this.state
    return(
      <div style={{margin:10}}>
        <NodeInfo info={info}/>
        <Timeline>
          {info && info.peers.map((peer)=>
             <Timeline.Item color={(peer.isAlive)?"green":"red"}>
               <Tag color="blue" onClick={()=>this.handleChange(peer.peer)}>{peer.peer}</Tag>
                <NodeInfo node={peer.peer}/>
             </Timeline.Item>
           )
          }
        </Timeline>
      </div> 
    )
  }
}

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
