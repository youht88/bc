import React from 'react'
import { Timeline } from 'antd';

export default class MyTimeline extends React.Component {
  constructor(props) {
    super(props);
    //this.state = { data: this.props.data };
    this.state={data:this.props.data}
  }
  componentDidUpdate(prevProps, prevState) {
    console.log("componentDidUpdate")
  }
  render() {
    const items= this.props.data.map((item,i)=>
           {
            return (<Timeline.Item key={i}> {item} </Timeline.Item>)
           })
    //const items1 = (<li> aaa </li>)
    console.log(_.keys(items))
    return (
      <Timeline>
        {items}
      </Timeline>
    );
  }
}
