FROM nginx:stable-alpine

ADD ./docker/assets/nginx/nginx.conf /etc/nginx/nginx.conf
ADD ./docker/assets/nginx/ssl/spot.kenyahmis.org.crt /etc/nginx/spot.kenyahmis.org.crt
ADD ./docker/assets/nginx/ssl/kenyahmis.org.key /etc/nginx/kenyahmis.org.key

RUN mkdir -p /var/www/html

EXPOSE 80 443

RUN addgroup -g 1000 laravel && adduser -G laravel -g laravel -s /bin/sh -D laravel

RUN chown laravel:laravel /var/www/html
