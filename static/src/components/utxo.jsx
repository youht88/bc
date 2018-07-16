  import React from 'react'
  
  import moment from 'moment';
  import { Row, Col ,Icon,message} from 'antd';
  import {Link} from 'react-router-dom'
  
  import {Table,Divider,Collapse} from 'antd'
  const Panel = Collapse.Panel;
  
  import { Form, Input, Button ,Tag} from 'antd';
  const FormItem = Form.Item;
  
  import {Modal} from 'antd';
  
  class UtxoTable extends React.Component{
    constructor(props){
      super(props)
      this.state={visible:false,script:"",utxoData:[],total:0}
      this.setData = this.setData.bind(this)
    }
    componentDidMount(){
      this.ajaxGet(this.props.type,(data)=>{
            this.setData(data)
      })
    }
    ajaxGet(path,cb){
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
    ajaxPost(path,data,cb){
      $.ajax({
        type: 'POST',    // 请求方式
        data: data,
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
               "script" :item[j].txout.script,
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
    onClick(text){
      this.setState({script:text,visible:true})
    }
    handleCheck(){
      this.ajaxPost('check/script',{script:this.state.script},(value)=>{
            alert(value)
      })
    }
    handleOk(){
      this.setState({visible:false})
    }
    render(){
      const columns = [{
        title: 'hash',
        dataIndex: 'txHash',
        key: 'txHash',
        render: text => <Link to={`/transaction/${text}`}>{text.substr(0,6)+'...'}</Link>,
      },{
        title: '索引',
        dataIndex: 'index',
        key: 'index',
      },{
        title: '地址',
        dataIndex: 'outAddr',
        key: 'outAddr',
        render: text => <Link to={`/wallet/${text}`}><Tag color={'#'+text.substr(0,6)}>{text.substr(0,6)+'...'}</Tag></Link>,
      },{
        title: '金额',
        dataIndex: 'amount',
        key: 'amount',
      },{
        title: '脚本',
        dataIndex: 'script',
        key: 'script',
        render: text => text ? <Icon type="file-text" style={{color:"blue"}} onClick={this.onClick.bind(this,text)}/> : <Icon type="file" style={{color:"#ddd"}}/>,
      }];
      
      const {utxoData} = this.state
      if (utxoData){
        return(
          <div> 
           <Collapse defaultActiveKey={['0']} >
            <Panel header={<div><h4>{this.props.type}</h4>
                           <Tag color="red">总金额:{this.state.total}</Tag></div>} key={0}>
              <Table dataSource={utxoData} columns={columns} pagination={false}/>
            </Panel>
           </Collapse>
           <Modal
              title="脚本"
              visible={this.state.visible}
              cancelText="检查"
              okText="关闭"
              closable={false}
              onOk={this.handleOk.bind(this)}
              onCancel={this.handleCheck.bind(this)}
            >
              <pre>{this.state.script}</pre>
            </Modal>
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
  
  
