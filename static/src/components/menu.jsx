import React from 'react'
import { Menu, Icon, Button } from 'antd';
import { Link } from 'react-router-dom';
const SubMenu = Menu.SubMenu;

export default class MyMenu extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      collapsed: false,
    }
    this.toggleCollapsed=this.toggleCollapsed.bind(this)
  }

  toggleCollapsed() {
      this.setState({
       collapsed: !this.state.collapsed,
      });
  }
  render() {
    return (
      <div >
        <Button type="primary" onClick={this.toggleCollapsed} style={{ marginBottom: 16 }}>
          <Icon type={this.state.collapsed ? 'menu-unfold' : 'menu-fold'} />
        </Button>
        <Menu
          defaultSelectedKeys={['1']}
          defaultOpenKeys={['sub1']}
          mode="inline"
          theme="dark"
          inlineCollapsed={this.state.collapsed}
        >
          <Menu.Item key="1">
            <Icon type="pie-chart" />
            <span><Link to="/home">Home</Link></span>
          </Menu.Item>
          <Menu.Item key="2">
            <Icon type="desktop" />
            <span><Link to="/steps">Wallet</Link></span>
          </Menu.Item>
          <Menu.Item key="3">
            <Icon type="inbox" />
            <span><Link to ="/card">Blockchain</Link></span>
          </Menu.Item>
          <SubMenu key="sub1" title={<span><Icon type="mail" /><span>Node</span></span>}>
            <Menu.Item key="5">List</Menu.Item>
            <Menu.Item key="6">Register</Menu.Item>
            <Menu.Item key="7">Gossip</Menu.Item>
            <Menu.Item key="8">PBFT</Menu.Item>
          </SubMenu>
          <SubMenu key="sub2" title={<span><Icon type="appstore" /><span>Blockchain</span></span>}>
            <Menu.Item key="9">
              <Link to="/block">Block</Link>
            </Menu.Item>
            <SubMenu key="sub3" title="Transaction">
              <Menu.Item key="11">UTXO</Menu.Item>
              <Menu.Item key="12">
                <Link to = "/transaction">Transaction</Link>
              </Menu.Item>
              <Menu.Item key="13">MerkleTree</Menu.Item>
            </SubMenu>
          </SubMenu>
        </Menu>
      </div>
    );
  }
}

