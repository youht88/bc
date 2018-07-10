import React from 'react'

import moment from 'moment';
import { Row, Col ,Icon,message,notification} from 'antd';
import {Link} from 'react-router-dom'

import {Table,Divider,Collapse} from 'antd'
const Panel = Collapse.Panel;

import { Form, Input, Button ,Tag} from 'antd';
const FormItem = Form.Item;

class FormWalletAddress extends React.Component {
  constructor() {
    super();
    this.handleSubmit = this.handleSubmit.bind(this)
  }
  componentDidMount() {
    // To disabled submit button at the beginning.
    //this.props.form.validateFields();
  }
  
  handleAjax(url,path,cb){
    $.ajax({
      type: 'GET',    // 请求方式
      url: `http://${url}/${path}`,
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
  
  handleSubmit(e){
    e.preventDefault();
    this.props.form.validateFields((err,values)=>{
      if(err){
        message.error("请输入正确的blockHash.")
        return
      }
      if (this.props.onSubmit){
        let address = values.walletAddress
        if (address.length!=64){
          this.handleAjax(this.props.url,`wallet/getAddress/${address}`,
            (value)=>{
              this.props.onSubmit(value)
            }
           ) 
        }else{
          this.props.onSubmit(address)
        }
      }
    });
        
  }

  render() {
    const { getFieldDecorator} = this.props.form;
    return (
      <div>
        <Form layout="inline">
          <FormItem
            label="钱包地址"
          >
          {getFieldDecorator('walletAddress', {
            rules: [
              {required: true, message: '请输入钱包地址' }],
          })(
             <Input style={{width:400}}placeholder="input wallet address" />
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
const WrappedForm = Form.create()(FormWalletAddress)
 
class UtxoTable extends React.Component{
  constructor(props){
    super(props)
    this.state={utxoData:[],total:0}
    this.setData = this.setData.bind(this)
  }
  componentDidMount(){
    this.handleAjax(this.props.url,this.props.type,(data)=>{
          this.setData(data)
    })
  }
  componentWillReceiveProps(nextProps){
    this.handleAjax(nextProps.url,nextProps.type,(data)=>{
          this.setData(data)
    })
  }
  handleAjax(url,path,cb){
    $.ajax({
      type: 'GET',    // 请求方式
      url: `http://${url}/${path}`,
      success: (res, status, jqXHR)=> {
        cb(res)
      },
      error: (res,status,error)=>{
        // 控制台查看响应文本，排查错误
        message.error(`http://${url}/${path}错误,请输入正确的地址`);
      }
    })
  }
  setData(data){
    let utxoData=[]
    let total=0
    const utxoSet = data
    for(let txHash in utxoSet){
      const item = utxoSet[txHash]
      for(let j in item){
        total = total + item[j].txout.amount    
        utxoData.push({
           "txHash":txHash,
           "index":item[j].index,
           "outAddr":item[j].txout.outAddr,
           "amount" :item[j].txout.amount,
           "key":txHash+j
        })
      }
    }
    this.setState({utxoData:utxoData})
    this.setState({total:total})
  }
  render(){
    const columns = [{
      title: 'txHash',
      dataIndex: 'txHash',
      key: 'txHash',
      render: text => <Link to={`/transaction/${text}`}>{text.substr(0,6)+'...'}</Link>,
    },{
      title: 'index',
      dataIndex: 'index',
      key: 'index',
    },{
      title: 'outAddr',
      dataIndex: 'outAddr',
      key: 'outAddr',
      render: text => <a href="javascript:;"><Tag color={'#'+text.substr(0,6)}>{text.substr(0,6)+'...'}</Tag></a>,
    },{
      title: 'amount',
      dataIndex: 'amount',
      key: 'amount',
    }];
    
    const {utxoData} = this.state
    if (utxoData){
      return(
        <div>
         <Collapse defaultActiveKey={['0']} >
          <Panel header={<div><h3>{this.props.type}</h3><Tag color="red">总金额:{this.state.total}</Tag></div>} key={0}>
            <Table dataSource={utxoData} columns={columns} pagination={false}/>
          </Panel>
         </Collapse>
        </div>
        )
      }
    else {
      return null
    } 
  }
}
  
export default class Wallet extends React.Component{
    constructor(props){
      super(props)
      message.info(JSON.stringify(this.props.match.params))
      this.state = {walletAddress:      this.props.match.params.walletAddress}
      this.setWalletAddress = this.setWalletAddress.bind(this)
    }
    setWalletAddress(value){
      this.setState({walletAddress:value})
    }
    render(){
      const port = location.port == '7777' ? 5000 : location.port 
      const url = document.domain +":" + port
      return(
        <div>
          <WrappedForm url={url} onSubmit={this.setWalletAddress}/>
              <div>
                <UtxoTable url={url} type={`utxo/main/${this.state.walletAddress}`}/>     
                <UtxoTable url={url} type={`utxo/trade/${this.state.walletAddress}`}/>
                <UtxoTable url={url} type={`utxo/isolate/${this.state.walletAddress}`}/>
              </div>
        </div>
      )
  }
}
  
  
