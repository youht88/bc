import React from 'react';
import ReactDOM from 'react-dom';

import { Layout } from 'antd';
const { Header, Footer, Sider, Content } = Layout;

import MyMenu from './components/menu.jsx'
import Home from './components/home.jsx'
import StepsSample from './components/steps.jsx'
import Blockchain from './components/blockchain.jsx'
import Rater from './components/rate.jsx'
import MyTree from './components/tree.jsx'
import TxForm from './components/txForm.jsx'
import Block from './components/block.jsx'
import UTXO from './components/utxo.jsx'
import Wallet from './components/wallet.jsx'
import Node from './components/node.jsx'

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
              <Route path="/blockchain" component={Blockchain} />
              <Route path="/wallet/:walletAddress" component={Wallet} />
              <Route path="/wallet" component={Wallet} />
              <Route path="/transaction/:txHash" component={TxForm} />
              <Route path="/transaction" component={TxForm} />
              <Route path="/block/:blockHash" component={Block} />
              <Route path="/block" component={Block} />
              <Route path="/utxo" component={UTXO} />
              <Route path="/node" component={Node} />
              <Redirect to="/" />
            </Switch>
          </Content>
        </Layout>
        <Footer>
          <Route path="/blockchain" component={StepsSample} />
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