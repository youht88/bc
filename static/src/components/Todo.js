/*
var React=require('react')
import { DatePicker, message } from 'antd';

class Todo extends React.Component{
    constructor(props){
      super(props);
      this.state={
        date:'',
      }
    }
    render(){
     return(
      <div>
        <div style={{width:400,margin:'100px auto'}}>
          <DatePicker onChange={value=>this.handleChange(value)} />
          <div style={{marginTop:20}}>当前日期：{this.state.date.toString()}
          </div>
        </div>
        <h2>*****</h2>
        <h1>Hello {this.props.name}</h1>
      </div>
      )
    }
  }
*/
import { DatePicker, message } from 'antd';
class Todo extends React.Component{
    constructor(props){
      super(props);
      this.state={
        date:'',
      }
    }
    render(){
     return(
      <div>
        <div style={{width:400,margin:'100px auto'}}>
          <DatePicker onChange={value=>this.handleChange(value)} />
          <div style={{marginTop:20}}>当前日期：{this.state.date.toString()}
          </div>
        </div>
        <h2>*****</h2>
        <h1>Hello {this.props.name}</h1>
      </div>
      )
    }
  }

module.exports = Todo;