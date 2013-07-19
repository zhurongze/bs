
# bs

List bugs and reviews in OpenStack projects.

# Installation

    $git clone https://github.com/zhurongze/bs.git
    $cd bs
    $sudo python setup.py install

# Configuration



    $sudo mkdir /etc/bs
    $sudo vim /etc/bs/bs.conf

    [DEFAULT]
    gerrit_host = review.openstack.org
    gerrit_port = 29418
    gerrit_username = <yournam_in_gerrit>

    projects = nova,cinder,glance,keystone
    types = bug,review

**Ensure your SSH public key was added in review.openstack.org gerrit service.**

# Usage

    $bs
    ......
    (Cmd)help

## Example 

If you want list 10 lastest Nova bugs.

    (Cmd)nb 10

If you want wath the NO.5 bug detail.

    (Cmd)w 5

If you want list 20 lastest Cinder  reviews.

    (Cmd)cr 20

If you want wath the NO.6 reviews detail.

    (Cmd)w 6
