import React from 'react';
import moment from 'moment';
import { Row, Col ,message} from 'antd';
import { Card ,Avatar,Icon,Tag} from 'antd';
const { Meta } = Card;

import {Link} from 'react-router-dom';

import { Form, Input, Button } from 'antd';
const FormItem = Form.Item;

class FormRange extends React.Component {
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
        message.error("表单输入错误！")
        return
      }
      if (this.props.onSubmit){
        this.props.onSubmit(values)
      }
    });
        
  }

  render() {
    const { getFieldDecorator} = this.props.form;

    return (
      <div>
        <Form layout="inline">
          <FormItem
            label="from"
          >
          {getFieldDecorator('from', {
            initialValue:0,
            rules: [
              {required: true, message: 'Please input from number! eg.0' }],
          })(
            <Input placeholder="input from index" />
          )}
            
          </FormItem>
          <FormItem
            label="to"
          >
            {getFieldDecorator('to', {
              initialValue:0,
              rules: [
               {required: true, message: 'Please input to number! eg.1' }],
            })(
              <Input placeholder="input in index" />
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
const WrappedFormRange = Form.create()(FormRange)

export default class CardSample extends React.Component{
  constructor(props) {
    super(props);
    this.state={
      blockchain:[{hash:"abcde",prev_hash:"xyz",nonce:101,index:1,timestamp:"1529964580",diffcult:2,merkleRoot:"merkle",data:[{outs:[{outAddr:"ppp"}]}]}]
      }
    this.handleCard = this.handleCard.bind(this)
    this.onSubmit = this.onSubmit.bind(this)
    this.getData = this.getData.bind(this)
  }
  componentDidMount(){
    this.getData()
  }
  componentWillReceiveProps(props){
  }
  getData(from=0,to=0){
    const port = location.port=='7777' ? 5000 : location.port
    const url = document.domain + ':' + port
    message.warn(`http://${url}/blockchain/${from}/${to}`)
    $.ajax({
      type: 'GET',    // 请求方式
      url: `http://${url}/blockchain/${from}/${to}`,
      success: (res, status, jqXHR)=> {
        this.setState({blockchain:res})
      },
      error: (res,status,error)=>{
        // 控制台查看响应文本，排查错误
        message.error('请输入正确的地址');
      }
    })
  }
  onSubmit(range){
    this.getData(range.from,range.to)
  }
  handleCard(){
    return this.state.blockchain && this.state.blockchain.map((block,idx)=>{
      return (
        <Col key={idx}>
          <Card
          title={<div><h3>{block.index}-{block.nonce}</h3>
            <h5><strong>hash:</strong>
            <Link to={`/block/${block.hash}`}>{block.hash.substr(0,6)}...</Link></h5></div>}
          hoverable
          style={{backgroundColor:'#eee'}}
          >
          <p><strong>prevHash:</strong>
          <Link to={`/block/${block.prev_hash}`}>{block.prev_hash.substr(0,6)}...</Link></p>
          <p><strong>diffcult:</strong>{block.diffcult}</p>
          <p><strong>timestamp:</strong>{moment(block.timestamp,'X').fromNow()}</p>
          <p><strong>txCount:</strong>{block.data.length}</p>
          <p><strong>merkleRoot:</strong>{block.merkleRoot.substr(0,6)}...</p>
          <Meta
            avatar={<Avatar style={{backgroundColor: '#'+Math.floor(Math.random()*0xffffff).toString(16)}}>
              <Link to={`/wallet/${block.data[0].outs[0].outAddr}`}>
              {block.data[0].outs[0].outAddr.substr(0,6)}...
              </Link>
              </Avatar>}
          />
          </Card>
        </Col>
     )}
    )
  }

  render(){
    return(
     <div>
      <WrappedFormRange onSubmit={this.onSubmit.bind(this)}/>
      <br/>
      <Row type="flex" justify-content="space-between" align="top">
        {this.handleCard()}
      </Row>
    </div>
    )
  }
}
