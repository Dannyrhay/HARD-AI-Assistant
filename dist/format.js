/* Local-only Markdown rendering: no raw HTML or remote image loads. */
const hardMarkdown=window.markdownit({html:false,linkify:false,typographer:false,breaks:false});
hardMarkdown.validateLink=url=>/^https?:\/\//i.test(url);
hardMarkdown.renderer.rules.image=(tokens,i)=>hardMarkdown.utils.escapeHtml(tokens[i].content||'Image');
hardMarkdown.renderer.rules.link_open=(tokens,i,options,env,self)=>{tokens[i].attrSet('target','_blank');tokens[i].attrSet('rel','noopener noreferrer');return self.renderToken(tokens,i,options)};
function hardFormat(value){return DOMPurify.sanitize(hardMarkdown.render(String(value||'')),{ALLOWED_TAGS:['p','br','strong','em','s','h1','h2','h3','h4','h5','h6','ul','ol','li','blockquote','pre','code','hr','table','thead','tbody','tr','th','td','a'],ALLOWED_ATTR:['href','target','rel','start'],ALLOW_DATA_ATTR:false})}
