import React from 'react';
import ReactDOM from 'react-dom';

import { Layout } from 'antd';
const { Header, Footer, Sider, Content } = Layout;

import MyMenu from './components/menu.jsx'
import Home from './components/home.jsx'
import StepsSample from './components/steps.jsx'
import CardSample from './components/card.jsx'
import Rater from './components/rate.jsx'
import MyTree from './components/tree.jsx'
import MyTable from './components/table.jsx'
import Block from './components/block.jsx'

import {BrowserRouter,Route,Switch,Redirect,Link} from 'react-router-dom';


class App extends  React.Component{
  constructor(props) {
    super(props);
    this.state = { value: 3 };
    this.f1=this.f1.bind(this)
  }
  f1(){
    this.setState({value:5})
  }
  render() {
    var message =
      'React Flask Socket.io antd webpack...';
    return (<div>
      <Layout>
        <Header >
          <h1 style={{"color":"white"}}>{message}</h1>
        </Header>
        <Layout>
          <Sider style={{"color":"white"}}>
            <MyMenu/>
          </Sider>
          <Content style={{ margin: '24px 16px 0' }}>
            <Switch>
              <Route path="/" exact component={Home} />
              <Route path="/card" component={CardSample} />
              <Route path="/steps" component={StepsSample} />
              <Route path="/transaction" component={MyTable} />
              <Route path="/block/:blockHash" component={Block} />
              <Redirect to="/" />
            </Switch>
          </Content>
        </Layout>
        <Footer>
          <Route path="/card" component={StepsSample} />
        </Footer>
      </Layout>
      </div>
        );
  }
};

ReactDOM.render((
   <BrowserRouter>
     <App/>
   </BrowserRouter>
   ), document.getElementById("container"))