import React from 'react';
import {Table,Form, Input, Button,Divider,Tag,Icon,message,notification,Alert } from 'antd';
import {Link} from 'react-router-dom';
import moment from 'moment';

import TxForm from './txForm.jsx';
import MyEcharts from './echarts.jsx';

const FormItem = Form.Item;
const Search = Input.Search;
const {TextArea} = Input

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
      render: text => <Link to={`/wallet/${text}`}><Tag color={'#'+text.substr(0,6)}>{text.substr(0,6)+'...'}</Tag></Link>,
    },{
      title: <Icon type="clock-circle" style={{ fontSize: 16, color: '#08c' }} />,
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
        //for(var k=0;k<outs.length;k++){
        //  txAmount += outs[k].amount
        //}
        txAmount += outs[0].amount
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
    this.state={data:undefined,errText:null}
    this.handleSubmit = this.handleSubmit.bind(this)
    this.handleAjax = this.handleAjax.bind(this)
  }
  componentDidMount() {
  }
  handleAjax(path,data,cb){
    $.ajax({
      type: 'POST',    // 请求方式
      data:data,
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
  handleCheck(e){
    e.preventDefault();
    this.props.form.validateFields((err,values)=>{
      if(err){
        message.error("新交易表单输入错误！")
        return
      }
      if (values.script)
        this.handleAjax('check/script',{script:values.script},
           (data)=>{
              this.setState({errText:data})
              if (data=="True" || data=="False")
                message.success("check right.")
           }
        )
      else
        message.success("check right.")
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
      let path=`${values.inAddr}/${values.outAddr}/${values.amount}`
      this.handleAjax(encodeURI(`trade/${path}`),{script:values.script},
        (value)=>{
           if (typeof(value)=="object"){
             if (value.errCode)
               alert(value.errText)
             else
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
            label="金额"
          >
            {getFieldDecorator('amount', {
              rules: [
               {required: true, message: 'Please input amount' }],
            })(
              <Input placeholder="input amount" />
            )}
          </FormItem>
          <FormItem
            label="脚本"
          >
            {getFieldDecorator('script', {
              rules: [
               {required: false, message: 'Please input script' }],
            })(
              <TextArea rows={10} placeholder="input script" style={{color:"green",fontWeight:"bold",backgroundColor:'black'}} />
            )}
          </FormItem>
          <FormItem >
            <Button type="primary" onClick={this.handleCheck.bind(this)} style={{margin:10}}>检查</Button>
            <Button type="primary" onClick={this.handleSubmit} style={{margin:10}}>提交</Button>
          </FormItem>
        </Form>
      </div>
      {this.state.errText ? <Alert type="error" description={this.state.errText}></Alert> :null}
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
            <Input placeholder="input Any Hash" style={{width:"300px"}}/>
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

const data1 = [
        {name: "JavaScript",value:2},
        {name: "Java",value:1},
        {name: "HTML/CSS",value:3}
      ]
const data2 = [
        {name: "JavaScript",value:3,v2:9},
        {name: "Java",value:2,v2:6},
        {name: "HTML/CSS",value:1,v2:7}
      ]
const series1={
        type:"line",
        markPoint:
         {data:[{type:"max",name:"最大值"}]}
      }

class GraphForm extends React.Component{
  constructor(props) {
    super(props);
  }
  render(){
    const size={width:"400px",height:"300px"}
    return(
     <div>
      <Divider orientation="left"><h1>趋势与图表</h1></Divider>
      <MyEcharts type={"pie"} title={"编程语言"} data={data1} size={size}/>
      <MyEcharts type={"bar"} title={"语言2"} data={data2} size={size}/>
     </div>
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
