/* Independent source menu screenshot fixtures; no localized text hashes. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const fixtures=require('../audit/entry-art-fixtures.json').regions;
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
 try{
  const page=await browser.newPage({viewport:{width:1280,height:960}});
  await page.goto(process.env.CASHFLOW_TEST_URL||'http://127.0.0.1:3041');
  await page.waitForFunction(()=>document.body.classList.contains('native-scene-ready'));
  async function check(prefix){
   for(const fixture of fixtures.filter(f=>f.name.startsWith(prefix))){
    const png=await page.screenshot({clip:{x:128+fixture.stage_rectangle[0],y:25+fixture.stage_rectangle[1],width:fixture.stage_rectangle[2],height:fixture.stage_rectangle[3]}});
    const rgba=await page.evaluate(async data=>{const image=new Image();image.src='data:image/png;base64,'+data;await image.decode();const canvas=document.createElement('canvas');canvas.width=image.width;canvas.height=image.height;const context=canvas.getContext('2d');context.drawImage(image,0,0);return Array.from(context.getImageData(0,0,image.width,image.height).data)},png.toString('base64'));
    if(fixture.maximum_channel_error){
     const source=require('node:fs').readFileSync(require('node:path').join(__dirname,'../audit',fixture.source_file));
     assert.equal(crypto.createHash('sha256').update(source).digest('hex'),fixture.source_png_sha256);
     const expected=await page.evaluate(async ({data,rect})=>{const image=new Image();image.src='data:image/png;base64,'+data;await image.decode();const canvas=document.createElement('canvas');canvas.width=rect[2];canvas.height=rect[3];const c=canvas.getContext('2d');c.drawImage(image,128+rect[0],25+rect[1],rect[2],rect[3],0,0,rect[2],rect[3]);return Array.from(c.getImageData(0,0,rect[2],rect[3]).data)},{data:source.toString('base64'),rect:fixture.stage_rectangle});
     let maximum=0;for(let i=0;i<rgba.length;i++)maximum=Math.max(maximum,Math.abs(rgba[i]-expected[i]));
     assert.ok(maximum<=fixture.maximum_channel_error,fixture.name+' channel difference '+maximum);
    }else assert.equal(crypto.createHash('sha256').update(Buffer.from(rgba)).digest('hex'),fixture.rgba_sha256,fixture.name+' original pixels');
   }
  }
  await check('title');
  assert.equal(await page.locator('#online-panel').evaluate(e=>getComputedStyle(e).visibility),'hidden','lobby stays hidden behind title');
  await page.locator('#classic-title').click();
  await page.locator('#show-room-create').click();
  await check('create');
  assert.equal(await page.locator('.classic-create-instructions').evaluate(e=>getComputedStyle(e).color),'rgb(0, 0, 0)');
  await page.locator('#room-name').fill('图像核对');
  await page.locator('[data-room-capacity="1"]').click();
  await page.locator('#create-room').click();
  await page.locator('#waiting-player-name').waitFor();
  await check('waiting');
  assert.equal(await page.locator('.classic-waiting-instructions').evaluate(e=>getComputedStyle(e).color),'rgb(0, 0, 0)');
  await page.locator('#room-waiting [data-room-leave]').click();
  await page.locator('#classic-title').waitFor({state:'visible'});
  console.log('PASS original title artwork within one channel level; menu sheet edge and create/waiting player frames match exact independent source pixels; title isolation and source instruction colors.');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
