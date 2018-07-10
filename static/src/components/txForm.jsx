import React from 'react'

import moment from 'moment';
import { Row, Col ,Icon,message} from 'antd';
import {Link} from 'react-router-dom'

import {Table,Divider,Collapse} from 'antd'
const Panel = Collapse.Panel;

import { Form, Input, Button ,Tag} from 'antd';
const FormItem = Form.Item;
import {Alert} from 'antd';

class FormTXHash extends React.Component {
  constructor() {
    super();
    this.handleSubmit = this.handleSubmit.bind(this)
  }
  componentDidMount() {
    // To disabled submit button at the beginning.
    //this.props.form.validateFields();
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
        message.error(`http://${this.props.url}/${path}错误,请输入正确的地址`);
      }
    })
  }

  handleSubmit(e){
    e.preventDefault();
    this.props.form.validateFields((err,values)=>{
      if(err){
        message.error("请输入正确的transactionHash.")
        return
      }
      if (this.props.afterSubmit){
        this.handleAjax(`transaction/${values.txHash}`,(data)=>{
          this.props.afterSubmit(data)
        })
      }
    });
        
  }

  render() {
    const { getFieldDecorator} = this.props.form;
    return (
      <div>
        <Form layout="inline">
          <FormItem
            label="交易hash"
          >
          {getFieldDecorator('txHash', {
            rules: [
              {required: true, message: '请输入transactionHash' }],
          })(
             <Input style={{width:400}}placeholder="input transaction index" />
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
const WrappedForm = Form.create()(FormTXHash)

export default class TxForm extends React.Component{
  constructor(){
    super()
    const insColumns = [{
      title: 'prevHash',
      dataIndex: 'prevHash',
      key: 'prevHash',
      render: text => <Link to={`/transaction/${text}`}>{text.substr(0,6)+'...'}</Link>,
    },{
      title: 'index',
      dataIndex: 'index',
      key: 'index',
    }];
    const outsColumns = [{
      title: 'outAddr',
      dataIndex: 'outAddr',
      key: 'outAddr',
      render: text => <Link to={`/wallet/${text}`}><Tag color={'#'+text.substr(0,6)}>{text.substr(0,6)+'...'}</Tag></Link>,
    }, {
      title: 'amount',
      dataIndex: 'amount',
      key: 'amount',
    }];
    
    this.state = {insColumns,outsColumns}
    this.setData = this.setData.bind(this)
  }
  componentDidMount(){
    const {data}=this.props
    if (data) {
      this.setData(data)
    }else{
      const txHash = this.props.match.params.txHash
      if (txHash) {
        this.handleAjax(`transaction/${txHash}`,(data)=>{
          this.setData(data)
        })
      }
    }
  }
  handleAjax(path,cb){
    const port=location.port=='7777'?5000:location.port
    const url = document.domain + ':' + port
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
    if (data){
      let insData=[]
      let outsData=[]
      for(var i=0;i<data.insLen;i++){
       insData.push({
             "prevHash":data.ins[i].prevHash,
             "index":data.ins[i].index,
             "key":i
       })
      }
      for(var i=0;i<data.outsLen;i++){
       outsData.push({
             "outAddr":data.outs[i].outAddr,
             "amount" :data.outs[i].amount,
             "key":i
       })
      }
      this.setState({insData:insData})
      this.setState({outsData:outsData})
      this.setState({hash:data.hash,timestamp:data.timestamp,script:data.outs[0].script})
    }
    else {
      message.info("no data")
    }
  }
  handleSearchBar(){
    let url=this.props.url
    if (url==undefined){
      const port=location.port=='7777'?5000:location.port
      url = document.domain + ':' + port
    }
    return <WrappedForm url={url} afterSubmit={this.setData.bind(this)}/>
  }
  render(){
    const {hash,timestamp,insData,outsData,insColumns,outsColumns,script} = this.state
    if (insData){
      return(
      <div>
       <Collapse defaultActiveKey={['1']} >
        <Panel header={`交易哈希:${hash}`} key={this.props.idx}>
          <Row type="flex" justify="center" align="top" >
            <Col span={10}>
              <Table dataSource={insData} columns={insColumns} pagination={false}/>
            </Col>
            <Col span={4}>
              <Row type="flex" justify="center" align="middle">
              <span>
                <Icon type="double-right" style={{ fontSize: 20, color: '#080' }} />
                <Icon type="double-right" style={{ fontSize: 20, color: '#080' }} />
                <Icon type="double-right" style={{ fontSize: 20, color: '#080' }} />
                <Icon type="double-right" style={{ fontSize: 20, color: '#080' }} />
                <Icon type="double-right" style={{ fontSize: 20, color: '#080' }} />
              </span>
              </Row>
            </Col>  
            <Col span={10}>
              <Table dataSource={outsData} columns={outsColumns} pagination={false}/>
            </Col>
          </Row>
          <Alert type="info" description={<pre>{script?script:"No Script"}</pre>}></Alert>
        </Panel>
      </Collapse>
      </div>
      )
      }
    else {
      return this.handleSearchBar()

    }
  }
}
