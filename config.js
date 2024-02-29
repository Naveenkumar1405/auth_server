module.exports = {
    CLIENT_ID: process.env.CLIENT_ID || "c513e16bfad60ed5",
    CLIENT_SECRET: process.env.CLIENT_SECRET || "lNxtrRja7W9CtpYT8objV4aA4gxZcJvHyV6bwwZsuf3G",
    PERMITTED_REDIRECT_URLS: process.env.PERMITTED_REDIRECT_URLS ? process.env.PERMITTED_REDIRECT_URLS.split(",") : ["https://c2c-ap.smartthings.com/oauth/callback"],
    SESSION_SECRET: process.env.SESSION_SECRET || '123'
};