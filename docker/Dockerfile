FROM alpine 
MAINTAINER youht

RUN echo "#install python3"
RUN apk add python3 --no-cache
RUN pip3 install flask requests bash pyyaml
RUN apk add gcc g++ make libffi-dev openssl-dev --no-cache
RUN apk add python3-dev --no-cache
RUN pip3 install pycrypto

RUN apk add curl --no-cache
RUN apk add nodejs --no-cache

RUN npm init --yes
RUN npm install webpack webpack-cli -g --save
RUN npm install babel-core babel-preset-env babel-loader babel-preset-react --save
RUN echo {presets:[\'env\',\'react\']} > .babelrc
RUN npm install react react-dom --save
RUN npm install query underscore --save

WORKDIR /bc
