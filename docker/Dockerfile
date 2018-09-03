FROM alpine 
MAINTAINER youht

RUN echo "#install python3"
RUN apk add python3 --no-cache
RUN pip3 install flask flask-socketio requests bash pyyaml state_machine
RUN apk add gcc g++ make libffi-dev openssl-dev --no-cache
RUN apk add python3-dev --no-cache
RUN pip3 install pycrypto

RUN apk add curl --no-cache
RUN apk add nodejs --no-cache

RUN npm config set registry https://registry.npm.taobao.org
RUN npm init --yes
RUN npm install webpack webpack-cli --save-dev
RUN npm install webpack-dev-server  --save-dev

RUN npm install react react-dom --save
RUN npm install react-router react-router-dom --save
RUN npm install react-hot-loader --save-dev

RUN npm install style-loader css-loader url-loader --save-dev
RUN npm install html-webpack-plugin html-loader --save-dev
RUN npm install babel-core babel-preset-env babel-loader babel-preset-react --save-dev

RUN npm install babel-plugin-import --save-dev
RUN npm install antd --save

RUN npm install jquery underscore moment --save
RUN npm install socket.io socket.io-client --save

RUN echo {presets:[\'env\',\'react\']} > .babelrc

#patch
RUN pip3 install flask-cors pytz
RUN pip3 install socketio-client
RUN pip3 install pymongo bson

RUN npm install react-redux --save
RUN npm install echarts --save
WORKDIR /bc
