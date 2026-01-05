const gulp = require('gulp');

const gulpSass = require('gulp-sass');
const dartSass = require('sass');
const sass = gulpSass(dartSass);

const postcss = require('gulp-postcss');
const cssnano = require('cssnano');

const fg = require('fast-glob');
const sharp = require('sharp');
const path = require('path');
const fs = require('fs/promises');

const PATHS = {
  htmlSrc: 'frontend/index.html',
  htmlWatch: 'frontend/index.html',
  htmlDestDir: 'frontend/build',

  scssEntry: 'frontend/assets/scss/main.scss',
  scssWatch: 'frontend/assets/scss/**/*.scss',
  cssDest: 'frontend/build/css',

  jsSrc: 'frontend/assets/js/**/*.js',
  jsWatch: 'frontend/assets/js/**/*.js',
  jsDest: 'frontend/build/js',

  imgSrcDir: 'frontend/assets/img',
  imgGlob: 'frontend/assets/img/**/*.{png,jpg,jpeg}',
  imgWatch: 'frontend/assets/img/**/*.{png,jpg,jpeg}',
  imgDestDir: 'frontend/build/img',
};

async function buildHtml() {
  const html = await fs.readFile(PATHS.htmlSrc, 'utf8');

  // Cuando servimos frontend/build como raíz (/), los recursos viven en /css y /js
  const rewritten = html
    .replace('href="/build/css/main.css"', 'href="/css/main.css"')
    .replace('src="/build/js/app.js"', 'src="/js/app.js"');

  await fs.mkdir(PATHS.htmlDestDir, { recursive: true });
  await fs.writeFile(path.join(PATHS.htmlDestDir, 'index.html'), rewritten, 'utf8');
}

function buildCss() {
  return gulp
    .src(PATHS.scssEntry, { allowEmpty: false })
    .pipe(
      sass
        .sync({
          outputStyle: 'expanded',
          includePaths: ['frontend/assets/scss'],
        })
        .on('error', sass.logError)
    )
    .pipe(postcss([cssnano()]))
    .pipe(gulp.dest(PATHS.cssDest));
}

function buildJs() {
  return gulp.src(PATHS.jsSrc, { allowEmpty: true }).pipe(gulp.dest(PATHS.jsDest));
}

async function buildImg() {
  const inputFiles = await fg([PATHS.imgGlob], { dot: false });
  await Promise.all(
    inputFiles.map(async (inputPath) => {
      const rel = path.relative(PATHS.imgSrcDir, inputPath);
      const relDir = path.dirname(rel);
      const outDir = path.join(PATHS.imgDestDir, relDir);
      await fs.mkdir(outDir, { recursive: true });

      // Copia original
      const originalOut = path.join(PATHS.imgDestDir, rel);
      await fs.copyFile(inputPath, originalOut);

      const ext = path.extname(rel);
      const base = rel.slice(0, -ext.length);

      // WebP
      const outWebp = path.join(PATHS.imgDestDir, `${base}.webp`);
      await sharp(inputPath).webp({ quality: 82 }).toFile(outWebp);

      // AVIF
      const outAvif = path.join(PATHS.imgDestDir, `${base}.avif`);
      await sharp(inputPath).avif({ quality: 50 }).toFile(outAvif);
    })
  );
}

function watchAll() {
  gulp.watch(PATHS.htmlWatch, buildHtml);
  gulp.watch(PATHS.scssWatch, buildCss);
  gulp.watch(PATHS.jsWatch, buildJs);
  gulp.watch(PATHS.imgWatch, buildImg);
}

exports['build:css'] = buildCss;
exports['build:js'] = buildJs;
exports['build:img'] = buildImg;
exports['build:html'] = buildHtml;
exports.build = gulp.series(buildHtml, buildCss, buildJs, buildImg);
exports.watch = gulp.series(exports.build, watchAll);
exports.default = exports.build;
