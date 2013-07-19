import cmd
import os
import sys
import json
import paramiko
import pkg_resources
from oslo.config import cfg
from launchpadlib.launchpad import Launchpad

__version__ = pkg_resources.require('bs')[0].version

bs_opts = [
    cfg.StrOpt('gerrit_host',
               default='review.openstack.org',
               help='The host of gerrit service'),
    cfg.IntOpt('gerrit_port',
               default=29418,
               help='The port of gerrit service'),
    cfg.StrOpt('gerrit_username',
               default='',
               help='Username of gerrit service'),
    cfg.ListOpt('projects',
                default=['nova',
                         'cinder',
                         'keystone',
                         'glance',
                         'swift',
                         'neutron',
                         'horizon'],
                help='The targets of OpenStack'),
    cfg.ListOpt('types',
                default=['bug', 'review'],
                help='The data types'),
]


CONF = cfg.CONF
CONF(sys.argv[1:], project='bs', version=__version__)
CONF.register_opts(bs_opts)

project_map = {
    'n': 'nova',
    'c': 'cinder',
    'g': 'glance',
    'k': 'keystone',
    's': 'swift',
    'q': 'neutron',
    'h': 'horizon',
    'i': 'ironic',
    'm': 'ceilometer',
    't': 'trove',
    'e': 'heat',
    'o': 'oslo-incubator',
}

type_map = {
    'b': 'bug',
    'r': 'review',
}


def ssh_client(host, port, user=None, key=None):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()
    client.connect(host, port=port, key_filename=key, username=user)
    return client


def get_bugs(launchpad, project):
    return launchpad.projects[project].searchTasks(order_by='-datecreated')


def get_reviews(client, project):
    reviews = []

    while True:
        project_query = 'project:openstack/%s' % project
        query = [
            'gerrit', 'query', project_query, 'status:open', '(-Verified-1)',
            '--current-patch-set',
            'limit:100', '--commit-message', '--format=JSON']
        if reviews:
            query.append('resume_sortkey:%s' % reviews[-2]['sortKey'])
        stdin, stdout, stderr = client.exec_command(' '.join(query))

        for line in stdout:
            reviews.append(json.loads(line))
        if reviews[-1]['rowCount'] == 0:
            break

    return [x for x in reviews if 'id' in x]


class Colorize(object):
    NORMAL = '\033[0m'
    LINK = '\x1b[34m'

    @property
    def enabled(cls):
        return os.environ.get('CLICOLOR')

    def link(cls, s):
        return cls.LINK + s + cls.NORMAL if cls.enabled else s


def render_reviews(reviews, maximum=None):

    colorize = Colorize()

    if maximum > len(reviews):
        maximum = len(reviews)
    for i in xrange(maximum):
        review = reviews[i]
        print '{: >5}'.format(i), colorize.link(review['url']), \
                review['subject'].strip()


def render_bugs(objs, num):

    row_format = '|{index: >5}|{status: <15}|{title: <80}|{importance: <10}|\
            {date_created: <16}|'
    print row_format.format(index='index',
                            status='status',
                            title='title',
                            importance='importance',
                            date_created='date_created',
                            )
    print '-' * 130
    if num > len(objs):
        num = objs

    for i in xrange(num):
        o = objs[i]
        print row_format.format(
                index=i,
                status=o.status,
                title=o.title.split(': ')[1][1:-1][:80],
                importance=o.importance,
                date_created=o.date_created.strftime('%Y-%m-%d %H:%M'),
                )


class BS(cmd.Cmd):

    last_type = ''
    last_proj = ''
    lp_client = None
    ssh_client = None
    data = {}

    def get_data(self):
        for proj in CONF.projects:
            if 'bug' in CONF.types:
                print 'Get %s bugs......' % proj
                bugs = get_bugs(self.lp_client, proj)
                self.data[proj]['bug'] = bugs

            if 'review' in CONF.types:
                print 'Get %s reviews......' % proj
                reviews = get_reviews(self.ssh_client, proj)
                self.data[proj]['review'] = reviews

    def cmdloop(self):

        for proj in CONF.projects:
            self.data[proj] = {}

        print ''
        print "Please wait a few seconds, take a coffee :) "
        print '........'
        print "Get data from Launchpad and Gerrit"

        if 'bug' in CONF.types:
            self.lp_client = Launchpad.login_anonymously('testing',
                                                         'production',
                                                         version='devel')
        if 'review' in CONF.types:
            self.ssh_client = ssh_client(host=CONF.gerrit_host,
                                        port=CONF.gerrit_port,
                                        user=CONF.gerrit_username)

        self.get_data()
        print ''
        return cmd.Cmd.cmdloop(self)

    def format_print_list(self, proj, datatype, num):
        d = self.data[proj][datatype]

        if datatype == 'bug':
            render_bugs(d, num)
        elif datatype == 'review':
            render_reviews(d, maximum=num)

        self.last_type = datatype
        self.last_proj = proj

    def format_print_index(self, index):
        if not self.last_type or not self.last_proj:
            print "You need get data firstly"
            return
        else:
            d = self.data[self.last_proj][self.last_type]
            if index >= len(d):
                print "index exsize"
                return
            else:
                o = self.data[self.last_proj][self.last_type][index]

        colorize = Colorize()

        if self.last_type == 'bug':
            b = o.bug
            date = o.date_created.strftime('%Y-%m-%d %H:%M')
            print ""
            print "*" * 100
            print "Title: %s" % b.title
            print "Owners: {owner: <30}".format(owner=b.owner.display_name)
            print "Created: {date_created: <16}".format(date_created=date)
            print 'Status: {status: <15}'.format(status=o.status)
            print 'Importance: {im: <10}'.format(im=o.importance)
            if o.assignee:
                print 'Assignee: {a: <16}'.format(a=o.assignee.display_name)
            else:
                print 'Assignee:'
            print "Web_link: %s" % colorize.link(o.web_link)
            print "-" * 100
            print "Description:"
            print ""
            print b.description
            print ""
            for i in xrange(1, len(b.messages)):
                m = b.messages[i]
                print "{pre} {id: <2} {owner: <20} {post}".format(
                        pre='-' * 35,
                        id=i,
                        owner=m.owner.display_name[:20],
                        post='-' * 35)
                print m.content
                print ""
        elif self.last_type == 'review':
            print ""
            print "*" * 100
            print "Project: %s" % o['project']
            print "URL: %s" % colorize.link(o['url'])
            print "Status: %s" % o['status']
            print "OwnerName: %s" % o['owner']['name']
            print "OwnerEmail: %s" % o['owner']['email']
            print "Id: %s" % o['id']
            print "-" * 100
            print "commitMessage:"
            print "%s" % o['commitMessage']
            print "-" * 100
            print "reviewer:"
            for p in o['currentPatchSet']['approvals']:
                print "{n:<25} {t:<20} {v:<2}".format(n=p['by']['name'],
                                                      t=p['type'],
                                                      v=p['value'])

    def onecmd(self, cmdline):
        if not cmdline:
            return
        elif cmdline == 'quit':
            return True
        elif cmdline == 'version':
            print pkg_resources.require('bs')[0]
            return
        elif cmdline == 'help':
            help()
            return

        tokens = cmdline.split()
        if len(tokens) < 2:
            print "Error command! need paramter"
            return

        if tokens[0] == 'w':
            try:
                index = int(tokens[1])
            except:
                print "Error paramter, need a integer"
                return
            self.format_print_index(index)
            return

        cmds = list(tokens[0])
        short_proj = cmds[0]
        short_type = cmds[1]

        if (short_proj not in project_map or short_type not in type_map):
            print "Error command!"
            return

        proj = project_map[short_proj]
        datatype = type_map[short_type]

        if proj not in CONF.projects:
            print "This project does not exist!"
            return

        if datatype not in CONF.types:
            print "This type does not exist!"
            return

        self.format_print_list(proj, datatype, int(tokens[1]))

    def do_EOF(self, line):
        return True


def help():
    print ''
    print '### List a project data:'
    print '<project_shortname><datatype_shortname>  <number>'
    print ''
    print '### Watch a item:'
    print 'w <index>'
    print ''
    print '### Example:'
    print 'nb 10\t\t# List the lastest 10 bugs in Nova.'
    print 'w 1\t\t# Watch NO.1 bug in Nova.'
    print 'nr 10\t\t# List the lastest 10 reviews in Nova.'
    print 'w 4\t\t# Watch NO.4 review in Nova.'
    print ''

    print '### Project Map ShortName:'
    for s in project_map:
        print "%s:%s" % (s, project_map[s])
    print ''
    print '### DataType Map ShortName:'
    for d in type_map:
        print "%s:%s" % (d, type_map[d])
    print ''


def main():
    BS().cmdloop()


if __name__ == '__main__':
    BS().cmdloop()
