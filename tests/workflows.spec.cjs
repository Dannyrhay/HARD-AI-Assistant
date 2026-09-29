const {test,expect}=require('@playwright/test');
test('chat opens file workflow, copies with preview and offers persistent undo',async({page})=>{
 await page.goto('/');await page.getByPlaceholder('Message HARD…').fill('Find my latest proposal');await page.getByRole('button',{name:'Send message'}).click();
 await page.locator('[data-workflow]').click();await expect(page.getByRole('heading',{name:'Find a file'})).toBeVisible();await expect(page.locator('#list-files')).toContainText('proposal.txt');
 await page.locator('.file-menu summary').click();await page.getByRole('button',{name:'Organise file',exact:true}).click();await page.locator('#project-name').fill('Client project');
 page.once('dialog',d=>{expect(d.message()).toContain('Client project');d.accept()});await page.getByRole('button',{name:'Review file change'}).click();
 await page.getByText(/Undo recent file changes/).click();await expect(page.locator('[data-undo-file]')).toBeVisible();
 await page.reload();await page.locator('[data-workflow]').last().click();await page.getByText(/Undo recent file changes/).click();
 page.once('dialog',d=>d.accept());await page.locator('[data-undo-file]').first().click();await expect(page.locator('#list-files')).toContainText('1-1 of 1');
});
test('unsent chat, attachment and email survive reload; failed message retries',async({page})=>{
 await page.goto('/');await page.getByPlaceholder('Message HARD…').fill('Explain this attachment');await page.locator('#chat-upload').setInputFiles({name:'notes.txt',mimeType:'text/plain',buffer:Buffer.from('Synthetic notes')});
 await page.waitForResponse(r=>r.url().endsWith('/api/recovery')&&r.request().method()==='POST');await page.reload();
 await expect(page.getByPlaceholder('Message HARD…')).toHaveValue('Explain this attachment');await expect(page.locator('.attachment-card')).toContainText('notes.txt');
 await page.getByRole('button',{name:'Send message'}).click();await expect(page.getByRole('button',{name:'Retry answer'})).toBeVisible();
 await page.getByRole('button',{name:'Retry answer'}).click();await expect(page.locator('.chat-message.assistant').last()).toContainText('A saved fixture answer.');
 await page.getByPlaceholder('Message HARD…').fill('Prepare an email to client@gmial.com');await page.getByRole('button',{name:'Send message'}).click();await page.locator('[data-workflow]').last().click();
 await expect(page.locator('#recipient-email')).toHaveValue('client@gmial.com');await page.locator('#subject').fill('Unfinished proposal');await page.locator('#body').fill('Draft email body');
 await page.waitForResponse(r=>r.url().endsWith('/api/recovery')&&r.request().method()==='POST');await page.reload();await page.locator('[data-workflow]').last().click();await expect(page.locator('#subject')).toHaveValue('Unfinished proposal');
});
test('workspace backup downloads from settings',async({page})=>{
 await page.goto('/');await page.locator('#settings').click();await page.getByText('Backups and updates',{exact:true}).click();
 const pending=page.waitForEvent('download');await page.getByRole('button',{name:'Download workspace backup'}).click();const download=await pending;expect(download.suggestedFilename()).toMatch(/^HARD-backup.*zip$/);
});

test('email preflight warns on typos and preserves explicit review before saving',async({page})=>{
 await page.goto('/');await page.getByPlaceholder('Message HARD…').fill('Prepare an email to client@gmial.com');await page.getByRole('button',{name:'Send message'}).click();await page.locator('[data-workflow]').last().click();
 await page.locator('#recipient-name').fill('Example client');await page.locator('#recipient-confirm').check();await page.locator('#subject').fill('Proposal');await page.locator('#body').fill('Please review the attached fixture.pdf.');await page.locator('#attachment').selectOption({label:'fixture.pdf'});await page.locator('#visual').check();
 const warning=page.waitForEvent('dialog');await page.getByRole('button',{name:'Save draft and review'}).click();const dialog=await warning;expect(dialog.message()).toContain('Possible domain typo');await dialog.dismiss();await expect(page.getByRole('heading',{name:'Prepare an email'})).toBeVisible();
 page.once('dialog',d=>d.accept());await page.getByRole('button',{name:'Save draft and review'}).click();await expect(page.getByRole('heading',{name:'Check before sending'})).toBeVisible();await expect(page.getByText('client@gmial.com',{exact:true})).toBeVisible();
});
test('switching AI models preserves the unsent message',async({page})=>{
 await page.goto('/');await page.getByPlaceholder('Message HARD…').fill('Keep this draft');await page.locator('#chat-provider').selectOption({label:'Primary test'});await expect(page.getByPlaceholder('Message HARD…')).toHaveValue('Keep this draft');
});

test('conversion request opens document review and narrow layout stays usable',async({page})=>{
 await page.setViewportSize({width:520,height:740});await page.goto('/');await expect(page.getByPlaceholder('Message HARD…')).toBeVisible();while(await page.locator('.attachment-remove').count())await page.locator('.attachment-remove').first().click();await page.getByPlaceholder('Message HARD…').fill('Convert this to Word');await page.getByRole('button',{name:'Send message'}).click();await page.locator('[data-workflow]').last().click();
 await expect(page.getByRole('heading',{name:'Check a document',exact:true})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'test-results/narrow-documents.png',fullPage:true});
});
