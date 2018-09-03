const path = require('path')
const webpack = require('webpack');
const HtmlWebpackPlugin=require('html-webpack-plugin');
console.log(__dirname)
module.exports={
  entry: [
    'react-hot-loader/patch',
    path.resolve(__dirname, './src/index.js')
  ],
  output:{
      path: path.resolve(__dirname, 'dist'),
      publicPath:'/',
      filename  : '[name].js'
    },
  mode: "development",
  module:{
    rules:[
     {
        test: /\.css$/,
        loader: 'style-loader!css-loader'
      },
      {
        test: /\.(eot|svg|ttf|woff|woff2)(\?\S*)?$/,
        loader: 'file-loader'
      },
      {test:/\.(js|jsx)$/,
       exclude:/node_modules/,
       loader:'babel-loader',
       options:{
         presets:['env','react'],
         plugins: [
                  ['import', { libraryName: 'antd', libraryDirectory: 'es', style: 'css' }],
                ],
         // This is a feature of `babel-loader` for webpack (not Babel itself).
          // It enables caching results in ./node_modules/.cache/babel-loader/
          // directory for faster rebuilds.
          cacheDirectory: true,
         }
       },
    ]
  },
  plugins:[
    new HtmlWebpackPlugin({
      title:'webpack HMR test',
      template:'../templates/react.html'
    }),
    new webpack.NamedModulesPlugin(), // 新增
    new webpack.HotModuleReplacementPlugin(), //新增
    new webpack.ProvidePlugin({
        $:"jquery",
        jQuery:"jquery",
        "window.jQuery":"jquery",
        pio:"socket.io-client",
        _:"underscore",
        echarts:"echarts"
        })
  ],
  devServer:{
    contentBase: path.resolve(__dirname, 'dist'),
    disableHostCheck:true,
    publicPath:'/',
    compress:true,
    port:7777,
    host:'0.0.0.0',
    inline:true,
    hot:true,
    overlay:true
  }
}