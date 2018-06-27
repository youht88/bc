import React from 'react';
import moment from 'moment';
import { Row, Col ,message} from 'antd';
import { Card ,Avatar,Icon,Tag} from 'antd';
const { Meta } = Card;
import {Link} from 'react-router-dom'
import { Form, Input, Button } from 'antd';
const FormItem = Form.Item;

class FormBlockHash extends React.Component {
  constructor() {
    super();
    this.handleSubmit = this.handleSubmit.bind(this)
  }
  componentDidMount() {
    // To disabled submit button at the beginning.
    //this.props.form.validateFields();
  }
  handleSubmit(e){
    e.preventDefault();
    this.props.form.validateFields((err,values)=>{
      if(err){
        message.error("请输入正确的blockHash.")
        return
      }
      if (this.props.onSubmit){
        this.props.onSubmit(values.blockHash)
      }
    });
        
  }

  render() {
    const { getFieldDecorator} = this.props.form;
    return (
      <div>
        <Form layout="inline">
          <FormItem
            label="区块hash"
          >
          {getFieldDecorator('blockHash', {
            rules: [
              {required: true, message: '请输入blockHash' }],
          })(
             <Input style={{width:400}}placeholder="input block index" />
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
const WrappedForm = Form.create()(FormBlockHash)

import {Table,Divider} from 'antd'
import { Collapse } from 'antd';
const Panel = Collapse.Panel;

class TxForm extends React.Component{
  constructor(){
    super()
    const insColumns = [{
      title: 'prevHash',
      dataIndex: 'prevHash',
      key: 'prevHash',
      render: text => <a href="javascript:;">{text.substr(0,6)+'...'}</a>,
    },{
      title: 'index',
      dataIndex: 'index',
      key: 'index',
    }];
    const outsColumns = [{
      title: 'outAddr',
      dataIndex: 'outAddr',
      key: 'outAddr',
      render: text => <a href="javascript:;">{text.substr(0,6)+'...'}</a>,
    }, {
      title: 'amount',
      dataIndex: 'amount',
      key: 'amount',
    }];
    
    this.state = {insColumns,outsColumns}
  }
  componentDidMount(){
    const data=this.props.data
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
    }
    else {
      message.info("no data")
    }
  }

  render(){
    const {insData,outsData,insColumns,outsColumns} = this.state
    const {hash,timestamp} = this.props.data
    if (insData){
      return(
       <Collapse defaultActiveKey={['1']} >
        <Panel header={`TX HASH:${hash}`} key={this.props.idx}>
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
        </Panel>
      </Collapse>
      )
      }
    else {
      return null
    }
  }
}

export default class Block extends React.Component{
  constructor(props) {
    super(props);
    const blockHash=props.match.params.blockHash
    if (blockHash==undefined)
      this.state={
        blockHash:"00934f87ed5b4e6e1e05be12cb55a4cd54798a8a71610dc1ef93b21adadcfbb2",
        block:{hash:"00934f87ed5b4e6e1e05be12cb55a4cd54798a8a71610dc1ef93b21adadcfbb2",prev_hash:"0063b4cf5a31c98e17777c12db3ca6520fd7361895a271c1593f50961ea8c414",nonce:163,index:9,timestamp:"1529964580",diffcult:2,merkleRoot:"796e30249500449017abaeaf3b4cf207c464728c7d06250192198e510b542d40",data:[{outs:[{outAddr:"cadc9fa1926ef0b4d7d632b8cef183a5f65a8c511da565468aba3b83756ba8b3"}]}]}
        }
    else 
      this.state={blockHash:blockHash}
    this.blockHader = this.blockHader.bind(this)
    this.onSubmit = this.onSubmit.bind(this)
    this.getData = this.getData.bind(this)
  }
  componentDidMount(){
    this.getData(this.state.blockHash)
  }
  componentWillReceiveProps(props){
  }
  getData(blockHash){
    const port = location.port==7777 ? 5000:location.port
    const url = document.domain + ':' + port
    //message.warn(`http://${url}/blockchain/hash/${blockHash}`)
    $.ajax({
      type: 'GET',    // 请求方式
      url: `http://${url}/blockchain/hash/${blockHash}`,
      success: (res, status, jqXHR)=> {
        this.setState({block:res})
      },
      error: (res,status,error)=>{
        // 控制台查看响应文本，排查错误
        message.error('请输入正确的地址');
      }
    })
  }
  onSubmit(blockHash){
    this.getData(blockHash)
  }
  blockHader(){
    const {block} = this.state
    if (block){
      return (
          <Card
          title={<div><h2>BLOCK #{block.index}-{block.nonce}</h2>
            <h5><strong>hash:</strong>{block.hash}</h5></div>}
          hoverable
          style={{backgroundColor:'#eee'}}
          >
          <p><strong>prevHash:</strong>
           <div>{block.prev_hash}</div></p>
          <p><strong>diffcult:</strong>{block.diffcult}</p>
          <p><strong>timestamp:</strong>{moment(block.timestamp,'X').fromNow()}</p>
          <p><strong>txCount:</strong>{block.data.length}</p>
          <p><strong>merkleRoot:</strong>{block.merkleRoot}</p>
          <Meta
            avatar={<Avatar style={{backgroundColor: '#87d068'}}>
              {block.data[0].outs[0].outAddr.substr(0,4)+'...'}
              </Avatar>}
          />
          </Card>
      )}
    else {
       return null
    }
  }
  blockData(){
    const {block} = this.state
    if(block){
     return(
        block.data.map((data,idx)=>{
          return (
            <TxForm data={data} idx={idx}/>
          )
        })
     )
    }
    else {
      return null
    }
  }
  render(){
    return(
     <div>
      <WrappedForm onSubmit={this.onSubmit.bind(this)}/>
      <br/>
      {this.blockHader()}
      <br/>
      {this.blockData()}
    </div>
    )
  }
}
