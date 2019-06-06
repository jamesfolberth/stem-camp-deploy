# Setting up Webserver Stuff
We want to serve static webpages from `<example.com>` and the hub from `<hub.example.com>`(where example is replaced with your chosen domain name).
The configuration files in this directory set this up.
We expect to have ports 22, 80, and 443 open.
If the user goes to either site over HTTP, we redirect them to port 443 to use HTTPS.

We do all this in a few pieces:
 * Create SSL/TLS certificates with [Let's Encrypt](https://letsencrypt.org/).
 * Register a domain name and set up routing, including to the subdomain.
 * Install and configure `nginx`.

TODO JMF 22 May 2018: mention that user should change `example.com` in conf files

## Set up domain name and routing
1. Register a domain name `example.com` Amazon [Route 53](https://aws.amazon.com/route53/). Select all of the defaults.
2. Create a new [Elastic IP](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html) and associate it with the EC2 instance running the hub and `nginx`. 
   * Enter the EC2 dashboard.
   * Select 'Elastic IPs' from the sidebar menu
   * Select 'Allocate new address'
   * Choose 'Amazon Pool'
   * Right click on the newly created IP and select 'Associate address'
   * Associate the address to your Jupyterhub/NGINX instance.
   
   For now, the Jupyterhub instance will run the hub as well as serve static HTML, so we set up hosted zones to point to the elastic IP we allocated for the hub instance.
   We can change that later, though.

3. (this section needs to be checked)To point our domain (and subdomain) to the right IP, we need to configure two record sets under the auto generated hosted zone.
(See [set up the subdomain](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-routing-traffic-for-subdomains.html#dns-routing-traffic-for-subdomains-creating-hosted-zone) for more information).

4. Set the hosted zone to route to `example.com`.
    * Sign in to the [Route 53](https://console.aws.amazon.com/route53/home) console and click the "Hosted zones" from the navigation pane on the left.
    * Note that a hosted zone has been preconfigured for `example.com` when you registered the domain. Select this record. If you do not have a new zone, enter the following information into the corresponding fields and create the hosted zone:
      * For Domain Name, type your domain name (`example.com`).
      * For Comment, type text that describes what the subdomain does or is for.
      * For Type, choose Public.
      * Create the Host zone.
     
   * Click "Create Record Set" to point the domain to the elastic IP allocatd earlier.
     * Leave "Name" blank, since we're going to set up the base domain.
     * Leave "Type" as "A - IPv4 address"
     * Leave time to live (TTL) as 300 seconds
     * For "Value", enter the elastic IP allocated earlier and associated with the hub/`nginx` instance.
     * "Routing Policy" can be "Simple".
     * Click "Create"

   4.Create a record set for the Jupyterhub. Follow the previous step, but instead enter hub in the "Name" section.

## Setting up nginx and SSL
1. On the AMI we've used (one of the Amazon Linux flavors), `nginx` is in the repos, so install it with

   ```bash
   sudo yum install nginx
   sudo service nginx start
   ```
2. Test that njinx is running. Go to the EC2 instance in the AWS console, locate the jupyterhub instance and copy the Public DNS url into your web browser. There should be an Nginx basic page. Also note that Nginx has a [basic setup guide](https://www.nginx.com/blog/setting-up-nginx/).

3. Create the SSL/TLS certificate:
(!using certbot is far more efficient, we should remove all the files from the repo related to the source install)
   * If you don't have a domain name to use, generate a self-signed SSL certificate. A self-signed cert is quite okay for testing/development, but your browser will probably warn you about the cert when you navigate to your page.

    ```bash
    sudo mkdir /srv/jupyterhub/ssl
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /srv/jupyterhub/ssl/hub.key -out /srv/jupyterhub/ssl/hub.crt
    ```
   * If you do have a domain name to use, we install the certificates using Certbot. Go to the [Certbot website](https://certbot.eff.org/lets-encrypt/centosrhel7-other). The instructions for installation are well documented. You will choose Nginx and Centos7 for the options. Make sure to check that your cert was installed using the recommended site in the completetion text of the install. 

3. (seems to mee that this section is no longer relevant?)
Copy over the configuration files from this directory.
   These files are pretty much exactly the configuration files from [Jupyterhub's examples](http://jupyterhub.readthedocs.io/en/latest/config-examples.html).
   At the time of writing, they haven't written the AWS+NGINX
   We use a HTTP->HTTPS redirection from [Bjorn Johansen](https://www.bjornjohansen.no/redirect-to-https-with-nginx).

   Rename the default config.
   ```bash
   sudo su
   cd /etc/nginx/
   mv nginx.conf nginx.conf.bak
   ```
   Now copy (still as root) over `nginx.conf` to `/etc/nginx/nginx.conf`, and `conf.d` to `/etc/nginx/confg.d`.
   Edit these files to point to your SSL/TLS certs and D-H parameters.

4. The static HTML server expects files in `/data/www`.
   The proxy to the hub expects to the hub to be serving on port 8000 of the localhost.

5. Reload nginx files with `sudo nginx -s reload`.


   
## Register the project with Google OAuth 2.0

   We want to use Google's authentication system for our project.
   A lot of Jupyterhub deployments use GitHub authentication, which is good for their use-case (because their users likely already have GitHub accounts), but for us, Google is probably simpler.
   To do this, we want to create an OAuth 2.0 Client ID for our project, so the users can authenticate with their Google accounts.

   * Go to [Google API Manager](https://console.developers.google.com/apis/credentials), create a project, choose a name and submit
   * Under your new project, select credentials from the side menu, then select 'Domain Verification'. Under the important message, there is a link to the 'search console' to verify your domain. Select this link and follow the instructions.
   * Select 'Other' as your provider and follow the instructions. You will add the DNS instructions given as Record sets in your AWS console under the 'example.com' Hosted zone. Once your have completed the verification of your domain, return to the credentials page and type in 'hub.example.com' and submit.
   * Under 'Oauth Consent Screen', you'll need to set a meaningful, recognizable project name, as it will be displayed to the users when they authenticate. You will need to add `example.com` to your authorized domains list. Now save your settings 
   * Under the credentials dropdown, select 'create credentials' and select 'oauth client ID'. Choose 'web application', then set the authorized JS origins to `https://hub.example.com:443`, and the authorized callback URI to `https://hub.example.com:443/hub/oauth_callback`. Submit and copy down the Client ID and Secret for later configuration.

     - If you're using your own domain, set `OAUTH_CALLBACK_URL` in the Jupyterhub `start.sh` script.(To what? why 8443? Does the following bash script explain? Why not just mention the export line?)

        ```bash
        # Get the public hostname
        export EC2_PUBLIC_HOSTNAME=`ec2-metadata --public-hostname | sed -ne 's/public-hostname: //p'`
        if [ -z $EC2_PUBLIC_HOSTNAME ]; then
            echo "Error: Failed to get EC2 public hostname from `ec2-metadata`"
            exit 1
        else
            echo "Using EC2_PUBLIC_HOSTNAME=$EC2_PUBLIC_HOSTNAME"
        fi
        export OAUTH_CALLBACK_URL=https://${EC2_PUBLIC_HOSTNAME}:443/hub/oauth_callback
        ```
     - If you're using the EC2 public hostname (something like `ec2-{PUBLIC_IPv4}.us-west-2.compute.amazonaws.com`) instead of your own domain, you can use the following in `start.sh` to automatically set `OAUTH_CALLBACK_URL` to the current instance's public hostname.
           
        Note that you may have to update the authorized JS origin and callback URI on [Google API Manager](https://console.developers.google.com/apis/credentials) every time you stop/start the instance, as the restarted instance may be assigned a new DNS name.

   * Once you've created the Oauth Client ID, copy the client ID and secret to the file `/srv/jupyterhub/env`.

     ```bash
     # Google OAuth 2.0
     export OAUTH_CLIENT_ID=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA.apps.googleusercontent.com
     export OAUTH_CLIENT_SECRET=BBBBBBBBBBBBBBBBBBBBB
     ```

     Note that these are **secret**, and should not be pushed to a git repo or accessible for other users (hence the `chmod 700` when creating `/srv/jupyterhub` and why we source this file instead of hard-coding a config file in the repo).

Nginx is now set up. Move to the [Docker Swarm ReadMe](https://github.com/jamesfolberth/stem-camp-deploy/blob/ingoglia/swarm_legacy/README.md) for the next step in the setup.
