path = require('path')
module.exports={
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
                  ['import', { libraryName: 'antd', libraryDirectory: 'es', style: 'css' }]
                ],
           
          // This is a feature of `babel-loader` for webpack (not Babel itself).
          // It enables caching results in ./node_modules/.cache/babel-loader/
          // directory for faster rebuilds.
          cacheDirectory: true,
         }
       },
    ]
  },
  devServer:{
    contentBase: path.resolve(__dirname, 'dist'),
    compress:true,
    port:7777,
    host:'0.0.0.0',
    hot:true,
    inline:true,
    overlay:true
  }
}