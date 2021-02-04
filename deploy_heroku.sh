git config --global user.email 'tinaliou4@gmail.com'
git config --global user.name 'tinaliou4'
git init
heroku git:remote -a rbbcar-control
git add .
git commit -m "init."
git push heroku master
