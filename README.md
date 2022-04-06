After homework 2, you have a website where users can login to see profile page. Now let’s implement a real useful thing - a personal (or multi-user) blog website.

Basic part
Implement blog website features:

    A public "Story" page where everyone can see all blog posts
    Only authenticated user can add new post


Advanced part

    Post can have a theme image (and author name if your app is multi-user)
    Add visibility of the post (public/private) so guest can see only public posts (authenticated user can see his/her own private/public posts)
    Deploy your app using docker-compose (docker-compose.yaml will be evaluated)


Challenging part

    Implement editing and deleting post feature
    "Story" page automatically check and update for new posts


* Describe what you implemented in README.md
* Upload the code to a separate GitHub repository (https://github.com/itmo-wad/username-hw3)
* Submit the link to your work to Google Classroom assignment

i implemented basic part: 
  /feed page fro guests and /feed_auth page for authenticated user
  on posts can set visibility level for authenticated user only or guests and authenticated, add theme, text and picture 
  editing and deleting  post feature
