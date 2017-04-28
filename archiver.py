import praw, sys, re, json, time, os, logging, argparse, tarfile, shutil
from config import *

# SymVer
VERSION = "v0.1.0"

subredditName = None
startTime = int(time.time())
endTime = None


def usage():
    print(str(sys.argv[0]) + " <subreddit name>")


def cli_arguments():
    """ Process the command line arguments """
    global subredditName, OUTPUT_BASE, args
    parser = argparse.ArgumentParser(description='Archive the contents of a reddit subreddit.')
    parser.add_argument('subreddit', metavar='subreddit', type=str,
                        help='the subreddit name')
    parser.add_argument('--log', dest='loglevel', default="ERROR",
                        help='Logging Level')
    parser.add_argument('--output-dir', dest='OUTPUT_BASE', type=str, default=OUTPUT_BASE,
                        help='specify a new destination directory for the output')
    parser.add_argument('--no-wiki', dest='wiki', action='store_const', const=False, default=True,
                        help='don\'t archive the contents of the subreddit\'s wiki')
    parser.add_argument('--no-wiki-revisions', dest='wikiRevisions', action='store_const', const=False, default=True,
                        help='don\'t archive revisions of the subreddit\'s wiki pages')
    parser.add_argument('--no-submissions', dest='submissions', action='store_const', const=False, default=True,
                        help='don\'t archive the subreddit\'s submissions')
    parser.add_argument('--no-compress', dest='compress', action='store_const', const=False, default=True,
                        help='don\t compress the output')
    parser.add_argument('--keep', dest='keep', action='store_const', const=True, default=False,
                        help='keep the raw directory after compressing')

    args = parser.parse_args()

    OUTPUT_BASE = args.OUTPUT_BASE

    subredditName = re.sub(r'^\/?r\/?', "", str(args.subreddit))
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=numeric_level)

    return


def archive_wiki(subreddit, wikiDir, archiveRevisions = True):
    """ 
    Archive the wiki pages for the supplied subreddit 
    
    :param subreddit: A PRAW Subreddit object
    
    :param wikiDir: The path to the directory for the wiki pages
    
    """
    for wikipage in subreddit.wiki:
        logging.info("Processing Wiki Page: " + wikipage.name)
        try:
            pageFile = os.path.join(wikiDir, wikipage.name)
            if not os.path.isdir(os.path.dirname(pageFile)):
                os.makedirs(os.path.dirname(pageFile))
            # for revision in wikipage.revisions():
            #     print(revision['page'])
            with open(pageFile+".md", "w") as pageFileHandler:
                pageFileHandler.write(wikipage.content_md.encode('utf-8'))
                pageFileHandler.close()
            if archiveRevisions:
                for revision in wikipage.revisions():
                    logging.info("Processing Wiki Page: " + wikipage.name + " revision: " + revision['id'])
                    try:
                        with open('.'.join([pageFile, revision['id'], "md"]), "w") as pageRevisionFileHandler:
                            pageRevisionFileHandler.write(revision['page'].content_md.encode('utf-8'))
                            pageRevisionFileHandler.close()
                        time.sleep(SLEEP_SEC)
                    except Exception as revisionException:
                        logging.error("Ran into an Exception processing wiki page " + wikipage.name +
                              " revision " + revision['id'])
        except Exception as pageException:
            logging.error("Ran into an Exception processing wiki page " + wikipage.name)


def archive_submissions(subreddit, submissionDir):
    """
    Archive a subreddit's submissions
    :param subreddit:
    :param submissionDir:
    :return:
    """
    logging.info("Processing Submissions")
    count = 0
    if not os.path.isdir(submissionDir):
        os.makedirs(submissionDir)
    for submission in subreddit.submissions():
        logging.info("Processing Submission: " + submission.id)
        print(submission.id)
        count+=1
        submissionObj = {
            "id": submission.id,
            "shortlink": submission.shortlink,
            "fullname": submission.fullname,
            "approved_by": submission.approved_by,
            "archived": submission.archived,
            "author": {
                "name": submission.author.name,
                "flair": {
                    "css_class": submission.author_flair_css_class,
                    "text": submission.author_flair_text
                }
            },
            "banned_by": submission.banned_by,
            "brand_safe": submission.brand_safe,
            "contest_mode": submission.contest_mode,
            "created": submission.created,
            "created_utc": submission.created_utc,
            "distinguished": submission.distinguished,
            "domain": submission.domain,
            "downs": submission.downs,
            "edited": submission.edited,
            "gilded": submission.gilded,
            "hidden": submission.hidden,
            "is_self": submission.is_self,
            "likes": submission.likes,
            "flair": {
                "css_class": submission.link_flair_css_class,
                "text": submission.link_flair_text
            },
            "locked": submission.locked,
            "media": submission.media,
            "media_embed": submission.media_embed,
            "name": submission.name,
            "num_comments": submission.num_comments,
            "num_reports": submission.num_reports,
            "over_18": submission.over_18,
            "permalink": submission.permalink,
            "post_hint": submission.post_hint,
            "preview": submission.preview,
            "quarantine": submission.quarantine,
            "removal_reason": submission.removal_reason,
            "score": submission.score,
            "secure_media": submission.secure_media,
            "secure_media_embed": submission.secure_media_embed,
            "selftext": submission.selftext,
            "selftext_html": submission.selftext_html,
            "spoiler": submission.spoiler,
            "stickied": submission.stickied,
            "subreddit": {
                "name": submission.subreddit,
                "name_prefixed": submission.subreddit_name_prefixed,
                "type": submission.subreddit_type,
                "id": submission.subreddit_id,
            },
            "thumbnail": submission.thumbnail,
            "title": submission.title,
            "ups": submission.ups,
            "upvote_ratio": submission.upvote_ratio,
            "url": submission.url
        }
        with open(os.path.join(submissionDir, '.'.join([submission.id, "json"])), "w") as submissionFileHandler:
            submissionFileHandler.write(json.dumps(submissionObj))
    logging.info("Finished processing {0} submissions".format(count))
    pass


def archive_subreddit_information(subreddit, baseDir):
    """
    Archive basic information about the subreddit
    :param subreddit:
    :param baseDir:
    :return:
    """
    with open(os.path.join(baseDir, "rules.json"), "w") as rulesFileHandler:
        rulesFileHandler.write(json.dumps(subreddit.rules()))
    subredditObj = {
        "name": subreddit.display_name,
        "description": subreddit.description,
        "title": subreddit.title
    }
    with open(os.path.join(baseDir, subreddit.display_name + ".json"), "w") as fileHandler:
        fileHandler.write(json.dumps(subredditObj))
    pass


def write_meta(baseDir):
    """
    Write the archiveData.json meta data file to the archive for future reference
    :param baseDir:
    :return:
    """
    global startTime, subredditName, endTime, META_EXTRA
    metaData = {
        "archived_at": startTime,
        "started_at": startTime,
        "archived_with": "SubredditArchiver " + VERSION,
        "subreddit": subredditName,
        "command_line_arguments": args._get_kwargs()
    }
    if endTime:
        metaData['finished_at'] = endTime
    if META_EXTRA:
        metaData['extra_data'] = META_EXTRA
    with open(os.path.join(baseDir, "archiveData.json"), "w") as metaDataFileHandler:
        metaDataFileHandler.write(json.dumps(metaData))


def compress_archive(baseDir, startTime):
    """
    Create a compressed tarball of the archive.
    :param baseDir: 
    :param startTime: 
    :return: 
    """
    global subredditName
    workingDir = os.getcwd()
    try:
        os.chdir(os.path.dirname(baseDir)) # chdir to the output directory to combat tar extensive paths
        tarfileName = os.path.join('.'.join([subredditName, str(startTime), "tar.gz"]))
        with tarfile.open(tarfileName, "w:gz") as archiveFile:
            archiveFile.add(os.path.basename(baseDir))
            archiveFile.close()
    except Exception as e:
        logging.error("Something went wrong compressing the archive.")
    os.chdir(workingDir)

cli_arguments()
print("Archiving r/" + subredditName)

reddit = praw.Reddit(client_id=CLIENT_ID,
                     client_secret=CLIENT_SECRET,
                     user_agent = "subreddit-archiver:v0.1 (by /u/chpwssn github.com/chpwssn)")
reddit.read_only
subreddit = reddit.subreddit(subredditName)


# Build Paths
baseDir = os.path.abspath(os.path.join(OUTPUT_BASE, subredditName, str(startTime)))
wikiDir = os.path.join(baseDir, "wiki")
submissionDir = os.path.join(baseDir, "submissions")

if not os.path.exists(baseDir):
    os.makedirs(baseDir)

# Write Archive meta data
write_meta(baseDir)

archive_subreddit_information(subreddit, baseDir)

# Get Submissions
if args.submissions:
    archive_submissions(subreddit, submissionDir)

# Get Wiki Pages
if args.wiki:
    archive_wiki(subreddit, wikiDir, args.wikiRevisions)

# Log End Time and Rewrite Meta File
endTime = time.time()
write_meta(baseDir)

if args.compress:
    compress_archive(baseDir, startTime)
    if not args.keep:
        shutil.rmtree(baseDir)
