var FormItem = antd.Form.Item;
var Login = React.createClass({
  getInitialState: function() {
    return {
      username: "",
      userpass:"",
      namevalidateStatus:"",
      passvalidateStatus:"",
      lastvalidateStatus:"",
      nameHelp:"",
      passHelp:"",
      lastHelp:""
    };
  },
  handleUsernameChange: function (event) {
        this.setState({
            username: event.target.value
        });
    },
  handleUserpassChange: function (event) {
        this.setState({
            userpass: event.target.value
        });
    },
  handleSubmit: function(event) {
      if(this.state.username == ''){
          this.setState({
            namevalidateStatus: 'error',
            nameHelp:'请输入用户名！'
        });
      }
      else if(this.state.userpass == ''){
           this.setState({
            passvalidateStatus: 'error',
            passHelp:'请输入密码！'
        });
      }
      else{
         var obj = this;
           //提交表单数据到后端验证
          $.post("/loginAction",{
               username:this.state.username,
               userpass:this.state.userpass
              },
              function(data,status){
                var returnData = JSON.parse(data);
               if(returnData.infostatus=='T'){
                obj.setState({
                    lastvalidateStatus:"success",
                    lastHelp:returnData.infomsg
                  });
                location.href="/antd";
               }
               else {
                obj.setState({
                    userpass: '',
                    namevalidateStatus:"",
                    passvalidateStatus:"",
                    lastvalidateStatus:"error",
                    nameHelp:"",
                    passHelp:"",
                    lastHelp:returnData.infomsg
                  });
               }
              });
      }

     
      event.preventDefault();
  },
  render: function() {
    return (
        <antd.Form onSubmit={this.handleSubmit}  className="login-form">
              <h1>欢迎登录</h1>
              <FormItem validateStatus={this.state.namevalidateStatus} help={this.state.nameHelp}>
              <antd.Input className="username"  value={this.state.username} onChange={this.handleUsernameChange} prefix={<antd.Icon type="user" style={{ fontSize: 13 }} />}  placeholder="Username" />
              </FormItem>
              <FormItem validateStatus={this.state.passvalidateStatus} help={this.state.passHelp}>
              <antd.Input className="userpass"  value={this.state.userpass} onChange={this.handleUserpassChange}  prefix={<antd.Icon type="lock" style={{ fontSize: 13 }} />} type="password" placeholder="Password" />
              </FormItem>
              <FormItem validateStatus={this.state.lastvalidateStatus} help={this.state.lastHelp}>
              <antd.Checkbox>记住我</antd.Checkbox>
            <a className="login-form-forgot">忘记密码</a>
            <antd.Button type="primary" htmlType="submit" className="login-form-button">
              登录
            </antd.Button>
            <a>注册</a>
            </FormItem>
        </antd.Form>
    );
  }
});


ReactDOM.render(<Login />, document.getElementById('loginBox'));
