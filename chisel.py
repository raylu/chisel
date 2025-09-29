#!/usr/bin/env python2

# Chisel
# David Zhou
# 
# Requires:
# jinja2

import codecs, datetime, os, re, sys, time
import feedwerk.atom, jinja2, markdown2

#Settings
SOURCE = "./blog/" #end with slash
DRAFTS = "./drafts/"
DESTINATION = "./export/"
HOME_SHOW = 100 #numer of entries to show on homepage
TEMPLATE_PATH = "./templates/"
TEMPLATE_OPTIONS = {}
TEMPLATES = {
    'home': "home.html",
    'detail': "detail.html",
    'archive': "archive.html",
    'drafts': "drafts.html",
}
TIME_FORMAT = "%B %d, %Y"
ENTRY_TIME_FORMAT = "%m/%d/%Y"
#FORMAT should be a callable that takes in text
#and returns formatted text
FORMAT = lambda text: markdown2.markdown(text, extras=['fenced-code-blocks', 'footnotes'])
#########

STEPS = []

def step(func):
    def wrapper(*args, **kwargs):
        print("Starting " + func.__name__ + "...", end=' ')
        func(*args, **kwargs)
        print("Done.")
    STEPS.append(wrapper)
    return wrapper

def get_tree(source):
    files = []
    for root, ds, fs in os.walk(source):
        for name in fs:
            if name[0] == ".": continue
            path = os.path.join(root, name)
            f = open(path, "rU")
            title = f.readline()
            date = time.strptime(f.readline().strip(), ENTRY_TIME_FORMAT)
            year, month, day = date[:3]

            f.readline() # skip blank line
            fold = []
            lines = []
            seen_paragraph = False
            above_fold = True
            while True:
                line = f.readline().decode('utf-8')
                if line == '':
                    break
                lines.append(line)
                if line[0] == '\n' and seen_paragraph:
                    above_fold = False
                elif line[0] not in ['\n', '#']:
                    seen_paragraph = True
                if above_fold:
                    fold.append(line.rstrip())

            files.append({
                'title': title,
                'epoch': time.mktime(date),
                'fold_raw': ' '.join(fold).rstrip(),
                'fold': FORMAT('\n'.join(fold)),
                'content': FORMAT(''.join(lines)),
                'url': '/'.join([str(year), "%.2d" % month, "%.2d" % day, os.path.splitext(name)[0] + ".html"]),
                'pretty_date': time.strftime(TIME_FORMAT, date),
                'iso_date': time.strftime('%Y-%m-%d', date),
                'date': date,
                'year': year,
                'month': month,
                'day': day,
                'filename': name,
            })
            f.close()
    return files

def compare_entries(x, y):
    result = cmp(-x['epoch'], -y['epoch'])
    if result == 0:
        return -cmp(x['filename'], y['filename'])
    return result

def write_file(url, data):
    path = DESTINATION + url
    dirs = os.path.dirname(path)
    if not os.path.isdir(dirs):
        os.makedirs(dirs)
    with open(path, 'w') as file:
        file.write(data.encode('utf-8'))

@step
def generate_homepage(f, e):
    """Generate homepage"""
    template = e.get_template(TEMPLATES['home'])
    write_file("index.html", template.render(entries=f[:HOME_SHOW]))

@step
def master_archive(f, e):
    """Generate master archive list of all entries"""
    template = e.get_template(TEMPLATES['archive'])
    write_file("archives.html", template.render(entries=f))

@step
def atom_feed(f, e):
    feed = feedwerk.atom.AtomFeed('raylu', feed_url='https://blog.raylu.net/feed.atom',
            url='https://blog.raylu.net/', author='raylu')
    for entry in f:
        url = 'https://blog.raylu.net/' + entry['url']
        dt = datetime.datetime.fromtimestamp(entry['epoch'])
        feed.add(entry['title'].rstrip(), entry['fold'], url=url, updated=dt)
    write_file('feed.atom', feed.to_string())

@step
def detail_pages(f, e):
    """Generate detail pages of individual posts"""
    template = e.get_template(TEMPLATES['detail'])
    for file in f:
        write_file(file['url'], template.render(entry=file))

@step
def drafts(f, e):
    files = sorted(get_tree(DRAFTS), cmp=compare_entries)
    template = e.get_template(TEMPLATES['drafts'])
    write_file('drafts.html', template.render(entries=files))

@step
def robots_txt(f, e):
    write_file('robots.txt', 'User-agent: *\nDisallow:\n')

def main():
    print("Chiseling...")
    print("\tReading files...", end=' ')
    files = sorted(get_tree(SOURCE), cmp=compare_entries)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_PATH), **TEMPLATE_OPTIONS)
    print("Done.")
    print("\tRunning steps...")
    for step in STEPS:
        print("\t\t", end=' ')
        step(files, env)
    print("\tDone.")
    print("Done.")

if __name__ == "__main__":
    sys.exit(main())
