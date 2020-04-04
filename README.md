# svpsouthruislip.org.uk
Web site for the Saint Vincent de Paul Society at St. Gregory the Great Parish in South Ruislip, UK.

## Workflow for updating

The pages are written in markdown and compiled into HTML using [Selmer](https://github.com/yogthos/selmer) templates. You will need [Leiningen](https://github.com/technomancy/leiningen) 2.5.0 or above installed.

To run the site locally, change to the svpsouthruislip.org.uk directory and run:

``` bash
lein ring server
```

To create or edit a page or new blog post, first create a new branch. Write your content, reloading the site on your local machine periodically to check that everything looks OK (and the links work).

When you are finished, push the branch to github and create a pull request. Look it over again and, when satisfied, merge the pull request and delete the branch.

Github Actions will then take over and deploy the changes to AWS.
