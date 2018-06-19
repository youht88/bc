import React from 'react';
import ReactDOM from 'react-dom';

import { Layout } from 'antd';
const { Header, Footer, Sider, Content } = Layout;

import {Button} from 'antd';
import StepsSample from './components/steps.jsx'
import CardSample from './components/card.jsx'
import Rater from './components/rate.jsx'

class App extends  React.Component{
  render() {
    var elapsed = Math.round(this.props.elapsed  / 100);
    var seconds = elapsed / 10 + (elapsed % 10 ? '' : '.0' );
    var message =
      'React1 has been successfully running for ' + seconds + ' seconds.';

    return (<div>
        <h1 style={{"color":"white"}}>{message}
        </h1>
        </div>
        );
  }
};

var start = new Date().getTime();
var i=0
var t=setInterval(function() {
  if (i===10) {
    clearInterval(t)
  }
  i++
  ReactDOM.render(
    <div>
      <Layout>
        <Header>
          <App elapsed={new Date().getTime() - start} />
        </Header>
          <Layout>
            <Sider>
              <CardSample/>
            </Sider>
            <Content>
        <div>
        <Button id="download" type="primary" icon="download">下载</Button>
        <Button id="commit" type="primary" icon="swap">提交</Button>
        </div>
              <Rater/>
            </Content>
          </Layout>
        <Footer>
          <StepsSample/>
        </Footer>
      </Layout>
    </div>,
    document.getElementById('container')
  );
}, 100);
