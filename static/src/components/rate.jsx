import React from 'react';
import { Rate } from 'antd';

export default class Rater extends React.Component {
  constructor(props) {
    super(props);
    this.state = { value: 3 };
    this.handleChange=this.handleChange.bind(this)
  }
  handleChange(value) {
    this.setState({ value });
  }
  
  render() {
    const { value } = this.state;
    return (
      <span>
        <Rate onChange={this.handleChange} value={value} />
        {value && <span className="ant-rate-text">{value} stars</span>}
      </span>
    );
  }
}
