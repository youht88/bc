import React from 'react';
import {Table,Form, Input, Button,Divider,Tag,message,notification } from 'antd';
import {Link} from 'react-router-dom';
import moment from 'moment';

import TxForm from './txForm.jsx';

const FormItem = Form.Item;
const Search = Input.Search;

class BlockList extends React.Component{
  constructor(props) {
    super(props);
    const columns = [{
      title: '高度',
      dataIndex: 'index',
      key: 'index',
    },{
      title: 'Hash',
      dataIndex: 'hash',
      key: 'hash',
      render: text => <Link to={`/block/${text}`}>{text.substr(0,6)+'...'}</Link>,
    },{
      title: '交易数',
      dataIndex: 'txCnt',
      key: 'txCnt',
    },{
      title: '金额',
      dataIndex: 'txAmount',
      key: 'txAmount',
    },{
      title: '矿工',
      dataIndex: 'miner',
      key: 'miner',
      render: text => <Link to={`/wallet/${text}`}>{text.substr(0,6)+'...'}</Link>,
    },{
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: text => <Tag color="#2a4">{moment(text,"X").fromNow()}</Tag>,
    }];
    this.state={columns}
  }
  componentWillReceiveProps(nextProps) {
    if (nextProps.maxindex>0){
      let from,to
      to=nextProps.maxindex
      from = (to - 9)>=0 ? (to-9) : 0 
      this.handleAjax(`blockchain/${from}/${to}`,
        (value)=>{
          this.setState({blocks:value})
          this.handleData(value)        
        })
    }
  }
  handleAjax(path,cb){
    $.ajax({
      type: 'GET',    // 请求方式
      url: `http://${this.props.url}/${path}`,
      success: (res, status, jqXHR)=> {
        cb(res)
      },
      error: (res,status,error)=>{
        notification.error(
          {message:"出现错误",
           description:`http://${this.props.url}/${path}错误,请输入正确的地址`
          });
      }
    })
  }
  handleData(value){
    let data=[]
    for(var i=value.length-1;i>=0;i--){
      //txAmount
      let txAmount=0
      for(var j=0;j<value[i].data.length;j++){
        const outs=value[i].data[j].outs
        for(var k=0;k<outs.length;k++){
          txAmount += outs[k].amount
        }
      }
      //miner
      const miner = value[i].data[0].outs[0].outAddr
      data.push({
        "key":value[i].index,
        "index":value[i].index,
        "hash" :value[i].hash,
        "txCnt":value[i].data.length,
        "txAmount":txAmount,
        "miner":miner,
        "timestamp":value[i].timestamp
      })
    }
    this.setState({data})
  }
  render(){
    const {data,columns} = this.state
    return(
      <div>
        <Divider orientation="left"><h1>最近的十条交易</h1></Divider>
        <h2><Link to='/blockchain'>更多...</Link></h2>
        <Table dataSource={data} columns={columns}/>
      </div>
    )
  }
}
class TradeForm extends React.Component{
  constructor(props) {
    super(props);
    this.state={data:undefined}
    this.handleSubmit = this.handleSubmit.bind(this)
  }
  componentDidMount() {
  }
  handleAjax(path,cb){
    $.ajax({
      type: 'GET',    // 请求方式
      url: `http://${this.props.url}/${path}`,
      success: (res, status, jqXHR)=> {
        cb(res)
      },
      error: (res,status,error)=>{
        // 控制台查看响应文本，排查错误
        message.error(`http://${this.props.url}/${path}错误，请输入正确的地址`);
      }
    })
  }
  handleSubmit(e){
    e.preventDefault();
    this.props.form.validateFields((err,values)=>{
      if(err){
        message.error("新交易表单输入错误！")
        return
      }
      //message.warn(`trade/${values.inAddr}/${values.outAddr}/${values.amount}`)
      this.setState({data:undefined})
      this.handleAjax(`trade/${values.inAddr}/${values.outAddr}/${values.amount}`,
        (value)=>{
           if (typeof(value)=="object"){
             this.setState({data:value})
           }  
           else {
             //not have enough money
             this.setState({data:undefined})
             message.error(value)
           }
        }
      )
      
    });
        
  }
  render(){
    const { getFieldDecorator} = this.props.form;
    return(
     <div>
      <Divider orientation="left"><h1>发起新的交易</h1></Divider>
      <div>
        <Form>
          <FormItem
            label="钱包地址"
          >
            {getFieldDecorator('inAddr', {
            rules: [
              {required: true, message: 'Please input inAddr'}],
          })(
            <Input placeholder="input inAddr" />
          )}
          </FormItem>
          <FormItem
            label="转入地址"
          >
            {getFieldDecorator('outAddr', {
              rules: [
               {required: true, message: 'Please input outAddr' }],
            })(
              <Input placeholder="input outAddr" />
            )}
          </FormItem>
          <FormItem
            label="数字币"
          >
            {getFieldDecorator('amount', {
              rules: [
               {required: true, message: 'Please input amount' }],
            })(
              <Input placeholder="input amount" />
            )}
          </FormItem>
          <FormItem >
            <Button type="primary" onClick={this.handleSubmit}>确定</Button>
          </FormItem>
        </Form>
      </div>
      {this.state.data ? <TxForm data={this.state.data} idx={0}/> : null}
     </div>
    );
   }
}
const WrappedTradeForm = Form.create()(TradeForm)

class OneSearch extends React.Component{
  constructor(props) {
    super(props);
  }
  render(){
    const { getFieldDecorator} = this.props.form;
    return(
     <div>
       <Divider orientation="left"><h1>统一检索</h1></Divider>
       <div>
        <Form layout="inline">
          <FormItem
            label="地址"
          >
            {getFieldDecorator('inAddr', {
            rules: [
              {required: true, message: 'Please a Hash'}],
          })(
            <Input placeholder="input Any Hash" />
          )}
          </FormItem>
          <FormItem >
            <Button type="primary" onClick={this.handleSubmit}>检索</Button>
          </FormItem>
        </Form>
       </div>
     </div>
    )
  }
}
const WrappedOneSearch = Form.create()(OneSearch)

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
      (value)=>{
        this.setState({maxindex:value})
        notification.success(
          {message:"信息",
           description:`目前区块高度${value}`
           });
      })
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
        message.error(`${path}错误,请输入正确的地址`);
      }
    })
  }
   render(){
    const {url,maxindex} = this.state
    return(
       <div>
         <BlockList maxindex={maxindex} url={url}/>
         <WrappedTradeForm url={url}/>
         <WrappedOneSearch url={url}/>
         <GraphForm url={url}/> 
       </div>
     )
   }
}
