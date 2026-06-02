import http from 'http';

http.get('http://localhost:5001/health', (res) => {
  if (res.statusCode === 200) {
    process.exit(0);
  } else {
    process.exit(1);
  }
}).on('error', () => {
  process.exit(1);
});
