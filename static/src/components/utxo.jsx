  import React from 'react'
  
  import moment from 'moment';
  import { Row, Col ,Icon,message} from 'antd';
  import {Link} from 'react-router-dom'
  
  import {Table,Divider,Collapse} from 'antd'
  const Panel = Collapse.Panel;
  
  import { Form, Input, Button } from 'antd';
  const FormItem = Form.Item;
  
  class UtxoTable extends React.Component{
    constructor(props){
      super(props)
      this.state={utxoData:[],total:0}
      this.setData = this.setData.bind(this)
    }
    componentDidMount(){
      this.handleAjax(this.props.type,(data)=>{
            this.setData(data)
      })
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
    setData(data){
      if (data.summary!=undefined){
        let utxoData=[]
        const utxoSet = data.utxoSet
        for(let txHash in utxoSet){
          const item = utxoSet[txHash]
          for(let j in item){   
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
        this.setState({total:data.summary.total})
      }
      else {
        message.info("no data")
      }
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
        render: text => <Link to={`/wallet/${text}`}>{text.substr(0,6)+'...'}</Link>,
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
            <Panel header={this.props.type+','+this.state.total} key={0}>
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
  
export default class UTXO extends React.Component{
    constructor(props){
      super(props)
    }
    render(){
      const port = location.port == '7777' ? 5000 : location.port 
      const url = document.domain +":" + port
      return(
        <div>
          <UtxoTable url={url} type={"utxo/get"}/>     
          <UtxoTable url={url} type={"utxo/get/trade"}/>
          <UtxoTable url={url} type={"utxo/get/isolate"}/> 
        </div>
      )
  }
}
  
  
