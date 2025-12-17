const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const cron = require('node-cron');
const FormData = require('form-data');
const fs = require('fs');

// Configuration
const ADMIN_NUMBERS = ['2348155512886', '2348161592613','2348023796914','13263211372777@lid','72494786556097@lid'];
const API_URL = 'http://localhost:8000';

// Initialize WhatsApp client
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

// QR Code generation
client.on('qr', (qr) => {
    console.log('🔲 Scan this QR code with Ejide Pharmacy WhatsApp:');
    qrcode.generate(qr, { small: true });
});

// Client ready
client.on('ready', () => {
    console.log('✅ Ejide Pharmacy Bot is ready!');
    console.log('📱 24/7 Customer engagement active');
    console.log('💊 Medication reminders enabled');
    console.log('📊 Predictive analytics ready');
    console.log('🛒 Smart shopping cart active');
    scheduleAutomatedTasks();
});

// Handle incoming messages
client.on('message', async (message) => {
    try {
        const phoneNumber = message.from.replace('@c.us', '');
        const isAdmin = ADMIN_NUMBERS.includes(phoneNumber);
        
        console.log(`📨 ${isAdmin ? '👑 Admin' : '👤 Customer'} ${phoneNumber}: ${message.body.substring(0, 50)}`);

        // Handle CSV file uploads (admin only)
        if (isAdmin && message.hasMedia) {
            const media = await message.downloadMedia();
            
            if (media.mimetype === 'text/csv' || 
                media.mimetype === 'application/vnd.ms-excel' ||
                message.body.toLowerCase().includes('.csv')) {
                
                await handleCSVUpload(media, message);
                return;
            }
        }

        

        // Send text message to API
        const response = await axios.post(`${API_URL}/chat`, {
            phone_number: phoneNumber,
            message: message.body.trim(),
            is_admin: isAdmin,
            timestamp: new Date().toISOString()
        });

        const reply = response.data.reply;
        
        // Send reply
        await message.reply(reply);
        
        console.log(`✅ Replied to ${phoneNumber}`);
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        await message.reply('Sorry, I encountered an error. Please try again.');
    }
});

// Handle CSV upload
async function handleCSVUpload(media, message) {
    try {
        console.log('📤 Processing CSV upload...');
        
        const csvPath = './temp_inventory.csv';
        const buffer = Buffer.from(media.data, 'base64');
        fs.writeFileSync(csvPath, buffer);
        
        const form = new FormData();
        form.append('file', fs.createReadStream(csvPath));
        
        const response = await axios.post(
            `${API_URL}/upload-inventory`,
            form,
            {
                headers: {
                    ...form.getHeaders()
                }
            }
        );
        
        await message.reply(response.data.reply);
        
        fs.unlinkSync(csvPath);
        
        console.log('✅ CSV processed successfully');
        
    } catch (error) {
        console.error('❌ CSV upload error:', error.message);
        await message.reply('❌ CSV upload failed. Format:\n\ndrug_name,quantity,price,category,description,dosage_days,dosage_frequency');
    }
}

// Schedule automated tasks
function scheduleAutomatedTasks() {
    
    // Medication reminders (Every day at 9 AM and 7 PM)
    cron.schedule('0 9,19 * * *', async () => {
        console.log('💊 Running medication reminder checks...');
        
        try {
            const response = await axios.get(`${API_URL}/medication-reminders`);
            const reminders = response.data.reminders;
            
            for (const reminder of reminders) {
                const chatId = reminder.phone_number + '@c.us';
                await client.sendMessage(chatId, reminder.message);
                console.log(`✅ ${reminder.reminder_type} reminder sent to ${reminder.phone_number}`);
                
                // Add delay to avoid rate limiting
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
            
            console.log(`✅ Sent ${reminders.length} medication reminders`);
        } catch (error) {
            console.error('❌ Error sending medication reminders:', error.message);
        }
    });
    
    console.log('⏰ Medication reminders scheduled (9 AM & 7 PM daily)');
    
    // Weekly reports (Every Sunday at 8 PM)
    cron.schedule('0 20 * * 0', async () => {
        console.log('📊 Generating weekly reports...');
        
        try {
            const response = await axios.get(`${API_URL}/generate-weekly-report`);
            const report = response.data.report;
            
            for (const adminNumber of ADMIN_NUMBERS) {
                const chatId = adminNumber + '@c.us';
                await client.sendMessage(chatId, report);
                console.log(`✅ Weekly report sent to ${adminNumber}`);
            }
        } catch (error) {
            console.error('❌ Error sending weekly reports:', error.message);
        }
    });
    
    console.log('⏰ Weekly reports scheduled (Sundays 8 PM)');
    
    // Daily analytics digest for admins (Every day at 8 AM)
    cron.schedule('0 8 * * *', async () => {
        console.log('📈 Generating daily analytics digest...');
        
        try {
            // Send morning analytics summary to admins
            const greeting = `🌅 *GOOD MORNING!*

📊 Your daily analytics digest is ready.

Reply with:
• "analytics" - Full predictive insights
• "inventory report" - Stock analysis
• "weekly report" - Week summary

Have a productive day! 💪`;
            
            for (const adminNumber of ADMIN_NUMBERS) {
                const chatId = adminNumber + '@c.us';
                await client.sendMessage(chatId, greeting);
            }
            
            console.log('✅ Morning digest sent to admins');
        } catch (error) {
            console.error('❌ Error sending morning digest:', error.message);
        }
    });
    
    console.log('⏰ Daily analytics digest scheduled (8 AM)');
}

// Error handling
client.on('auth_failure', () => {
    console.error('❌ Authentication failed. Delete .wwebjs_auth and rescan.');
});

client.on('disconnected', (reason) => {
    console.log('⚠️ Client disconnected:', reason);
});

// Initialize client
console.log('🚀 Starting Ejide Pharmacy Bot...');
console.log('📋 Features enabled:');
console.log('   ✅ 24/7 WhatsApp engagement');
console.log('   ✅ AI-powered inventory management');
console.log('   ✅ Automated medication reminders');
console.log('   ✅ Smart shopping cart');
console.log('   ✅ Predictive analytics');
console.log('   ✅ On-demand admin reports');
console.log('');
client.initialize();