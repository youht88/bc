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

RUN npm init --yes
RUN npm install webpack webpack-cli -g --save-dev
RUN npm install webpack-dev-server -g --save-dev

RUN npm install react react-dom --save
RUN npm install react-router --save
RUN npm install react-hot-loader --save-dev

RUN npm install style-loader css-loader url-loader --save-dev
RUN npm install babel-core babel-preset-env babel-loader babel-preset-react --save-dev
RUN echo {presets:[\'env\',\'react\']} > .babelrc


RUN npm install babel-plugin-import --save-dev
RUN npm install antd --save

RUN npm install query underscore moment --save

WORKDIR /bc
