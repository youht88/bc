import React from 'react';

export default class MyEcharts extends React.Component{
  constructor(props) {
    super(props);
    //this.setOption = this.setOption.bind(this)
    this.initChart = this.initChart.bind(this)
  }
  componentDidMount() {
    this.initChart();
  }
  componentDidUpdate() {
    this.initChart();
  }
  initChart() {
    const {type,title,data,links,option,others} = this.props
    
    let myChart = echarts.init(this.refs.testChart)
    let options = this.setOption(type,title,data,links,option,others)
    myChart.setOption(options)
  }
  setOption(type,title,data,links,option,others){
    let options=null
    switch (type){
      case 'graph':
        options = {
          title:{
            text:title,
            left:"center"
          },
          tooltip:{},
          series : [
            {type:"graph",
             layout:'force',
             force:{
              repulsion:300,
              edgeLength:[100,250],
             },
             draggable:true,
             animation:true,
             edgeSymbol:['circle','arrow'],
             data:data,
             links:links,
            }
          ]
        }
        break
      case 'pie':
        options = {
          title:{
            text:title,
            left:"center"
          },
          series : [
            {
              type: 'pie',
              data: data,
              label: {
                normal: {
                  formatter: "{d}% \n{b}",
                }
              }
            }
          ]
        }
        break
      case 'bar':
        options = {
            title:{
              text:title,
              left:"left"
            },
            dataset:{
              source:data
            },
            tooltip:{},
            legend:{left:"right"},
            xAxis:{
              type:"category"
            },
            yAxis:{
              tpye:"value"
            },
            series : [
              {
                type: 'bar',
                label: {
                  normal: {
                    formatter: "{d}% \n{b}",
                  }
                }
              }
            ]
          }
        break
      case 'line':
        break
      default:
        options=option
        
    }
    return options 
  }
  render(){
    const {size} = this.props
    return(
      <div className="react-echarts">
        <div ref="testChart" style={size}>
        </div>
      </div>
    )
  }
}
