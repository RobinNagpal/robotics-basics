// CloudFront viewer-request function, attached to every behaviour.
//
// The site is a Next.js static export built with `trailingSlash: true`, so a
// page is a directory with an index.html inside it: /robotics-intro/ros/ros-intro/
// is the object .../ros-intro/index.html. S3 has no notion of an index
// document when it is read as a bucket rather than as a website endpoint —
// that is the price of keeping the bucket private behind Origin Access
// Control — so this function does the mapping instead.
//
// Three cases, in order:
//   /a/b/    -> rewrite to /a/b/index.html and fetch it
//   /x.svg   -> leave alone; it is a real object
//   /a/b     -> 301 to /a/b/ so each page has one URL
//
// The last one matters more than it looks. Serving a page at both /a/b and
// /a/b/ would split the cache and, worse, break every relative link inside it:
// a link to "c" resolves against /a/ from one and /a/b/ from the other.

function queryString(querystring) {
  var parts = [];
  for (var key in querystring) {
    var param = querystring[key];
    if (param.multiValue) {
      for (var i = 0; i < param.multiValue.length; i++) {
        parts.push(key + '=' + param.multiValue[i].value);
      }
    } else if (param.value === '') {
      parts.push(key);
    } else {
      parts.push(key + '=' + param.value);
    }
  }
  return parts.length ? '?' + parts.join('&') : '';
}

function handler(event) {
  var request = event.request;
  var uri = request.uri;

  // A directory: serve the index inside it. Covers "/" as well, which is the
  // site's front page.
  if (uri.endsWith('/')) {
    request.uri = uri + 'index.html';
    return request;
  }

  // A real file. Checked on the last segment rather than the whole path, so a
  // dot in a directory name higher up does not make a page look like a file.
  var lastSegment = uri.slice(uri.lastIndexOf('/') + 1);
  if (lastSegment.indexOf('.') !== -1) {
    return request;
  }

  // A page asked for without its trailing slash. Redirect rather than rewrite,
  // so the address bar and every relative link inside the page agree.
  return {
    statusCode: 301,
    statusDescription: 'Moved Permanently',
    headers: {
      location: { value: uri + '/' + queryString(request.querystring) },
    },
  };
}
