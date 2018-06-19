import React from 'react';
import { Steps } from 'antd';

const Step = Steps.Step;


export default class StepsSample extends React.Component{
   render(){
     return(
  <Steps current={0} status="process">
    <Step title="Finished" description="finish" />
    <Step title="it In Process" description="This is a description" />
    <Step title="Waiting" description="This is a description" />
  </Steps>      
     )
   }
}
