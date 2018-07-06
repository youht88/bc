import React from 'react'

import moment from 'moment';
import { Row, Col ,Icon,Spin,Alert,notification} from 'antd';
import {Link} from 'react-router-dom'

import {Table,Divider,Collapse} from 'antd'
const Panel = Collapse.Panel;

import { Form, Input, Button } from 'antd';
const FormItem = Form.Item;

import {Chart,Axis,Geom,Tooltip,Legend} from 'bizcharts';
import dataSet from "@antv/data-set"

notification.config({placement:'rightBottom'})  
class UtxoMain extends React.Component{
  constructor(props){
    super(props)
    this.state={utxoData:[],total:0,loading:true}
    this.setData = this.setData.bind(this)
  }
  componentDidMount(){
    this.handleAjax(this.props.type,(data)=>{
          notification.open({
             message:"通知",
             description:`目前累计：${data.summary.total}`
          })
         this.setData(data)
    })
  }
  handleAjax(path,cb){
    this.setState({loading:true})
    $.ajax({
      type: 'GET',    // 请求方式
      url: `http://${this.props.url}/${path}`,
      success: (res, status, jqXHR)=> {
        this.setState({loading:false})
        cb(res)
      },
      error: (res,status,error)=>{
        this.setState({loading:false})
        notification.open(
          {message:"出现错误",
           description:`http://${this.props.url}/${path}错误,请输入正确的地址`
           });
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
      notification.open({
        message:"no data"
      })
    }
  }
  render(){    
    const data=[
     {month:"Jan",temperature:-5,city:"大连"},
     {month:"Feb",temperature:0,city:"大连"},
     {month:"Mar",temperature:15,city:"大连"},
     {month:"Jan",temperature:1,city:"厦门"},
     {month:"Feb",temperature:15,city:"厦门"},
     {month:"Mar",temperature:20,city:"厦门"}
    ]
    return(
      <div>
      <Spin spinning={this.state.loading}>
        <Chart height={400} data={data} forceFit>
          <Legend/>
          <Axis name="month" />
          <Axis name="temperature" label={{formatter: val => `${val}°C`}}/>
          <Tooltip crosshairs={{type : "y"}}/>
          <Geom type="intervalStack" position="month*temperature"  color='city' />
        </Chart>
      </Spin>
      </div>
      )
  }
}

/*
{ ()=>{if (this.props.type == 'utxo/get'){
             return <h1>this.props.type</h1> 
          }else{
             return <h1>mmm</h1>
          }}
        }
*/
/*  
        <Chart height={400} data={data} forceFit>
          <Axis name="month" />
          <Axis name="temperature" label={{formatter: val => `${val}°C`}}/>
          <Tooltip crosshairs={{type : "y"}}/>
          <Geom type="line" position="month*temperature" size={2} color={'city'} />
          <Geom type="interval" position="month*temperature"  color={'city'} />
          <Geom type='point' position="month*temperature" size={4} shape={'circle'} color={'city'} style={{ stroke: '#fff', lineWidth: 1}} />
        </Chart>)

*/
export default class Wallet extends React.Component{
    constructor(props){
      super(props)
    }
    render(){
      const port = location.port == '7777' ? 5000 : location.port 
      const url = document.domain +":" + port
      return(
        <div>
          <Alert type="success" message="使用me代表服务器钱包地址" banner closable/>
          <UtxoMain url={url} type={"utxo/get"}/>     
          <UtxoMain url={url} type={"utxo/get/trade"}/>
          <UtxoMain url={url} type={"utxo/get/isolate"}/> 
        </div>
      )
    }
}
  
  

  
