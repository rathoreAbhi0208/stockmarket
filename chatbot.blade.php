@extends('layouts.dashboardLayout')
@section('title', 'liveChart')
@section('content')
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet" />
<link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
<script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>
<style>
	.sig_history1, .sig_history2, .sig_history3,.sig_history4, .sig_history7,.sig_history8,.detail-card{
	display: none !important;
	}
	.select2-container--default .select2-selection--single .select2-selection__rendered {
	line-height: 14px !important;
	}
	.container {
	background-color: #ffffff;
	border-radius: 1rem;
	box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
	padding: 2.5rem;
	/*max-width: 100%;*/
	max-width: 900px;
	margin: 0 auto;
	}
	.select2-container {
	width: 100% !important;
	}
	.message-box {
	padding: 1rem;
	border-radius: 0.75rem;
	margin-top: 1.5rem;
	font-weight: 600;
	display: flex;
	align-items: center;
	gap: 0.75rem;
	}
	.message-box.info { background-color: #e0f7fa; color: #006064; border: 1px solid #80deea; }
	.message-box.success { background-color: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
	.message-box.warning { background-color: #fff3e0; color: #ef6c00; border: 1px solid #ffcc80; }
	.message-box.error { background-color: #ffebee; color: #c62828; border: 1px solid #ef9a9a; }
	.analysis-section {
	border: 1px solid #edf2f7;
	border-radius: 0.75rem;
	padding: 1.5rem;
	margin-top: 1.5rem;
	background-color: #fcfcfc;
	box-shadow: inset 0 1px 3px 0 rgba(0,0,0,0.05);
	}
	.section-title {
	font-weight: 700;
	color: #2d3748;
	margin-bottom: 1rem;
	font-size: 1.25rem;
	border-bottom: 2px solid #e2e8f0;
	padding-bottom: 0.5rem;
	}
	.detail-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
	gap: 1rem;
	}
	.detail-card {
	background-color: #f7fafc;
	border: 1px solid #e2e8f0;
	border-radius: 0.5rem;
	padding: 1rem;
	display: flex;
	flex-direction: column;
	justify-content: space-between;
	min-height: 100px;
	}
	.detail-label {
	font-weight: 600;
	color: #4a5568;
	font-size: 0.95rem;
	margin-bottom: 0.25rem;
	}
	.detail-value-container {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	margin-top: 0.5rem;
	}
	.detail-value {
	color: #2d3748;
	font-size: 1.15rem;
	font-weight: 700;
	text-align: right;
	}
	.detail-date {
	color: #718096;
	font-size: 0.75rem;
	margin-top: 0.25rem;
	text-align: right;
	}
	.trade-recommendation {
	font-size: 1.15rem;
	padding: 1.5rem;
	margin-top: 2rem;
	border-radius: 0.75rem;
	font-weight: 600;
	line-height: 1.6;
	box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
	}
	.trade-recommendation.buy { background-color: #e6ffe6; color: #1b5e20; border: 2px solid #4caf50; }
	.trade-recommendation.sell { background-color: #ffebee; color: #b71c1c; border: 2px solid #f44336; }
	.trade-recommendation.neutral { background-color: #e3f2fd; color: #1565c0; border: 2px solid #2196f3; }
	ul { list-style-type: none; padding-left: 0; margin-top: 0.75rem; }
	ul li { position: relative; padding-left: 1.5rem; margin-bottom: 0.5rem; color: #4a5568; }
	ul li::before { content: '✔️'; position: absolute; left: 0; color: #4CAF50; font-size: 0.9rem; }
	.trade-recommendation.sell ul li::before { content: '❌'; color: #ef5350; }
	.trade-recommendation.neutral ul li::before { content: 'ℹ️'; color: #2196f3; }
	.spinner { border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 0 auto; }
	@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
	/* Chart and Toggle Styles */
	#chart-container {
	background-color: #ffffff;
	border-radius: 0.75rem;
	box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
	height: 500px;
	width: 100%;
	padding: 1rem;
	box-sizing: border-box;
	position: relative;
	display: none;
	}
	#chart { width: 100%; height: 100%; }
	.toggle-switch { position: relative; display: inline-block; width: 38px; height: 22px; }
	.toggle-switch input { opacity: 0; width: 0; height: 0; }
	.toggle-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; border-radius: 22px; }
	.toggle-slider:before { position: absolute; content: ""; height: 16px; width: 16px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; }
	input:checked + .toggle-slider { background-color: #2196F3; }
	input:focus + .toggle-slider { box-shadow: 0 0 1px #2196F3; }
	input:checked + .toggle-slider:before { transform: translateX(16px); }
	.select2-results__option
	{
	padding: 6px;
	user-select: none;
	-webkit-user-select: none;
	padding-left: 30px !important;
	}
</style>
<div class="container">
	<h1 class="text-3xl font-extrabold text-gray-900 mb-6 text-center tracking-tight">
		Advanced Stock Analysis
	</h1>
	<div class="mb-6">
		<label for="stockSelector" class="block text-gray-700 text-base font-bold mb-2">Select a Stock to Analyze:</label>
		<select id="stockSelector" class="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"></select>
	</div>
	<div id="loading" class="text-center mb-6 hidden">
		<div class="spinner"></div>
		<p class="text-gray-600 mt-3">Analyzing stock data...</p>
	</div>
	<div id="analysis-output" class="analysis-section hidden">
		<h2 class="section-title">Analysis for <span id="currentSymbolDisplay" class="text-blue-600"></span>  <span id="currentPriceDisplay" class="detail-value text-blue-700">N/A</span>
			<span id="currentPriceDate" class="detail-date"></span>
		</h2>
		<div class="detail-grid">
			<div class="detail-card">
				<span class="detail-label">Current Price:</span>
				<div class="detail-value-container">
					<span id="currentPriceDisplay" class="detail-value text-blue-700">N/A</span>
					<span id="currentPriceDate" class="detail-date"></span>
				</div>
			</div>
			<div class="detail-card">
				<span class="detail-label">Latest SMA Signal (10-Day):</span>
				<div class="detail-value-container">
					<span id="latestSmaSignalDisplay" class="detail-value">N/A</span>
					<span id="latestSmaSignalDate" class="detail-date"></span>
				</div>
			</div>
			<div class="detail-card">
				<span class="detail-label">Latest Swing High:</span>
				<div class="detail-value-container">
					<span id="latestSwingHighDisplay" class="detail-value">N/A</span>
					<span id="latestSwingHighDate" class="detail-date"></span>
				</div>
			</div>
			<div class="detail-card">
				<span class="detail-label">Latest Swing Low:</span>
				<div class="detail-value-container">
					<span id="latestSwingLowDisplay" class="detail-value">N/A</span>
					<span id="latestSwingLowDate" class="detail-date"></span>
				</div>
			</div>
			<div class="detail-card">
				<span class="detail-label">Market Structure 0.5 Fib (Latest):</span>
				<div id="msFibDetails" class="mt-1">N/A</div>
			</div>
			<div class="detail-card">
				<span class="detail-label">Overall Fibonacci 0.5 Level:</span>
				<div class="detail-value-container">
					<span id="overallFibDisplay" class="detail-value">N/A</span>
					<span id="overallFibDate" class="detail-date"></span>
				</div>
			</div>
		</div>
		<h2 style="display:none;" class="section-title mt-8">Trade Recommendation & Strategy</h2>
		<div id="tradeRecommendationOutput" class="trade-recommendation"></div>
		<h2 style="display:none;" class="section-title mt-8">Interactive Chart Analysis</h2>
		<div style="display:none;" class="mb-4 flex flex-wrap gap-x-6 gap-y-2 justify-center">
			<div class="flex items-center space-x-2">
				<label for="toggleSma" class="text-gray-700 text-sm">10-SMA</label>
				<label class="toggle-switch"><input type="checkbox" id="toggleSma" checked><span class="toggle-slider"></span></label>
			</div>
			<div class="flex items-center space-x-2">
				<label for="toggleOverallFib" class="text-gray-700 text-sm">Overall Fib</label>
				<label class="toggle-switch"><input type="checkbox" id="toggleOverallFib" checked><span class="toggle-slider"></span></label>
			</div>
			<div class="flex items-center space-x-2">
				<label for="toggleMarketStructureFib" class="text-gray-700 text-sm">MS Fib</label>
				<label class="toggle-switch"><input type="checkbox" id="toggleMarketStructureFib" checked><span class="toggle-slider"></span></label>
			</div>
			<div class="flex items-center space-x-2">
				<label for="toggleSwingPoints" class="text-gray-700 text-sm">Swing H/L</label>
				<label class="toggle-switch"><input type="checkbox" id="toggleSwingPoints" checked><span class="toggle-slider"></span></label>
			</div>
			<div class="flex items-center space-x-2">
				<label for="toggleSmaSignals" class="text-gray-700 text-sm">SMA Signals</label>
				<label class="toggle-switch"><input type="checkbox" id="toggleSmaSignals" checked><span class="toggle-slider"></span></label>
			</div>
			<div class="flex items-center space-x-2">
				<label for="togglePreviousMSFib" class="text-gray-700 text-sm">Previous MS Fib</label>
				<label class="toggle-switch"><input type="checkbox" id="togglePreviousMSFib" checked><span class="toggle-slider"></span></label>
			</div>
		</div>
		<div id="chart-container">
			<div id="chart"></div>
		</div>
	</div>
</div>
<script type="module">
	const TWELVE_DATA_API_KEY = 'pNfPaAqCCLW5TIyeNfmbJ9CaocjvSfNb'; // Your Twelve Data API Key
	
	// --- Global Data Holders ---
	let currentStockData = null; // Raw candle data
	let currentSMA = null;       // SMA data and signals
	let currentSwingPoints = null; // Swing high/low data
	let currentMarketStructure = null; // Market Structure Fib data
	let currentOverallFib = null;    // Overall Fib data
	let currentPrice = null;     // Current live price
	let previousMarketStructures = []; // Array to store previous market structures
	
	// --- Chart Variables ---
	let chart, candleSeries, smaSeries;
	let overallFibonacciLines = [];
	let marketStructureFibonacciLines = [];
	let previousMarketStructureLines = [];
	let swingHighMarkers = [];
	let swingLowMarkers = [];
	let smaSignalMarkers = [];
	
	function showMessageBox(msg, type, targetId = 'error-message') {
	    const messageBox = $(`#${targetId}`);
	    messageBox.removeClass().addClass(`message-box ${type}`).html(msg).removeClass('hidden');
	}

	function hideMessageBox(targetId = 'error-message') {
	    $(`#${targetId}`).addClass('hidden');
	}

	async function loadSymbolsFromApi(exchange = 'NSE') {
	const apiUrl = `https://basilstar.com/data/nse_bse_symbols.json`; // Your filtered list
	try {
	const response = await fetch(apiUrl);
	const data = await response.json();
	const dropdown = $('#stockSelector');
	dropdown.empty();
	
	if (!Array.isArray(data) || data.length === 0) {
	    showMessageBox(`No symbols available for ${exchange}.`, 'error');
	    return;
	}
	
	data.forEach(stock => {
	    if ((exchange === 'NSE' && stock.symbol.endsWith('.NS')) ||
	        (exchange === 'BSE' && stock.symbol.endsWith('.BO'))) {
	        dropdown.append(`<option value="${stock.symbol}">${stock.name} (${stock.symbol})</option>`);
	    }
	});
	
	dropdown.select2({ placeholder: `Search stocks in ${exchange}...`, allowClear: true });
	
	const defaultSymbol = dropdown.val();
	if (defaultSymbol) await analyzeStock(defaultSymbol);
	else {
	    $('#analysis-output').addClass('hidden');
	    showMessageBox('Please select a stock to begin analysis.', 'info');
	}
	
	dropdown.on('change', async function () {
	    if ($(this).val()) await analyzeStock($(this).val());
	});
	
	} catch (error) {
	showMessageBox(`Failed to load local symbol list.`, 'error');
	}
	}
	
	
	
	async function fetchHistoricalCandles(symbol) {
	const toDate = new Date().toISOString().split('T')[0];
	const fromDate = new Date();
	fromDate.setFullYear(fromDate.getFullYear() - 1); // 1 year back
	const fromStr = fromDate.toISOString().split('T')[0];
	
	const apiUrl = `https://financialmodelingprep.com/api/v3/historical-chart/1day/${symbol}?from=${fromStr}&to=${toDate}&apikey=pNfPaAqCCLW5TIyeNfmbJ9CaocjvSfNb`;
	
	const response = await fetch(apiUrl);
	const data = await response.json();
	
	if (!Array.isArray(data) || data.length === 0) {
	throw new Error(`No daily data found for ${symbol}.`);
	}
	
	return data.reverse().map((item, index) => ({
	time: item.date.split(' ')[0],
	open: parseFloat(item.open),
	high: parseFloat(item.high),
	low: parseFloat(item.low),
	close: parseFloat(item.close),
	index: index
	})).filter(item => !isNaN(item.open) && !isNaN(item.high) && !isNaN(item.low) && !isNaN(item.close));
	}
	
	
	async function fetchCurrentPrice(symbol) {
	const apiUrl = `https://financialmodelingprep.com/api/v3/quote/${symbol}?apikey=pNfPaAqCCLW5TIyeNfmbJ9CaocjvSfNb`;
	const response = await fetch(apiUrl);
	const data = await response.json();
	
	if (!Array.isArray(data) || data.length === 0 || !data[0].price) {
	console.warn(`Could not fetch current price for ${symbol}`);
	return null;
	}
	
	return parseFloat(data[0].price);
	}
	
	
	function calculateSMA(data, period = 10) {
	    const sma = [];
	    if (data.length < period) return [];
	    for (let i = period - 1; i < data.length; i++) {
	        const sum = data.slice(i - period + 1, i + 1).reduce((acc, val) => acc + val.close, 0);
	        sma.push({ time: data[i].time, value: sum / period });
	    }
	    return sma;
	}
	
	
	function detectSMASignals(data, smaData, smaPeriod = 10) {
	    const signals = [];
	    for (let i = 1; i < smaData.length; i++) {
	        const priceIndex = i + smaPeriod - 1;
	        const prevPriceIndex = i + smaPeriod - 2;
	        if (!data[priceIndex] || !data[prevPriceIndex]) continue;
	
	        if (data[prevPriceIndex].close < smaData[i-1].value && data[priceIndex].close > smaData[i].value) {
	            signals.push({ time: data[priceIndex].time, type: 'Buy', price: data[priceIndex].close });
	        } else if (data[prevPriceIndex].close > smaData[i-1].value && data[priceIndex].close < smaData[i].value) {
	            signals.push({ time: data[priceIndex].time, type: 'Sell', price: data[priceIndex].close });
	        }
	    }
	    return signals;
	}
	
	function findSwingHighLows(data, lookback = 5) {
	    const swingHighs = [];
	    const swingLows = [];
	
	    for (let i = lookback; i < data.length - lookback; i++) {
	        let isHigh = true;
	        for (let j = 1; j <= lookback; j++) {
	            if (data[i - j].high > data[i].high || data[i + j].high > data[i].high) {
	                isHigh = false;
	                break;
	            }
	        }
	        if (isHigh) {
	            swingHighs.push({ price: data[i].high, time: data[i].time, index: i });
	        }
	
	        let isLow = true;
	        for (let j = 1; j <= lookback; j++) {
	            if (data[i - j].low < data[i].low || data[i + j].low < data[i].low) {
	                isLow = false;
	                break;
	            }
	        }
	        if (isLow) {
	            swingLows.push({ price: data[i].low, time: data[i].time, index: i });
	        }
	    }
	    return {
	        latestHigh: swingHighs.length > 0 ? swingHighs[swingHighs.length - 1] : null,
	        latestLow: swingLows.length > 0 ? swingLows[swingLows.length - 1] : null,
	        allHighs: swingHighs,
	        allLows: swingLows
	    };
	}
	
	function getFibs(_top, _bot, _dir) {
	    const levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1];
	    const fibValues = {};
	    const rng = Math.abs(_top - _bot);
	
	    levels.forEach(level => {
	        let value;
	        if (_dir === 1) { // Bullish Fib: Retracement from Low (0) to High (1)
	            value = _bot + (rng * level);
	        } else { // Bearish Fib: Retracement from High (0) to Low (1)
	            value = _top - (rng * level);
	        }
	        fibValues[level.toFixed(3)] = value;
	    });
	    return fibValues;
	}
	
	function calculateMarketStructure(data) {
	    const structureLen = 5; // Smaller lookback for more reactive structure detection
	
	    const swingPoints = findSwingHighLows(data, structureLen);
	    const allHighs = swingPoints.allHighs;
	    const allLows = swingPoints.allLows;
	
	    if (allHighs.length < 1 || allLows.length < 1) {
	        return null; // Not enough swing points to define a structure
	    }
	
	    const lastHigh = allHighs[allHighs.length - 1];
	    const lastLow = allLows[allLows.length - 1];
	
	    if (!lastHigh || !lastLow) return null;
	
	    let structureTop, structureBottom, dir;
	
	    if (lastHigh.time > lastLow.time) {
	        dir = 1; // Bullish structure
	        structureBottom = lastLow.price;
	        structureTop = lastHigh.price;
	    } else {
	        dir = -1; // Bearish structure
	        structureTop = lastHigh.price;
	        structureBottom = lastLow.price;
	    }
	
	    if (structureTop < structureBottom) {
	        [structureTop, structureBottom] = [structureBottom, structureTop]; // Swap if inverted
	        dir = dir * -1; // Reverse direction if points were swapped, to maintain fib logic
	    }
	
	    const startIndex = Math.min(lastHigh.index, lastLow.index);
	    const endIndex = data.length - 1;
	
	    const fibLevels = getFibs(structureTop, structureBottom, dir);
	    const fib0_5 = fibLevels["0.500"];
	    const currentClose = data[data.length - 1].close; // Use latest candle close
	    const breakout = currentClose > fib0_5 ? 'above 0.5' : 'below 0.5';
	
	    return {
	        type: dir === 1 ? 'bullish' : 'bearish',
	        time: data[data.length - 1].time, // Current bar's time
	        top: structureTop,
	        bottom: structureBottom,
	        fib0_5_level: fib0_5,
	        breakout: breakout,
	        allLevels: fibLevels,
	        startIndex: startIndex,
	        endIndex: endIndex
	    };
	}
	
	function findPreviousMarketStructures(data, count = 10) {
	    const structures = [];
	    const structureLen = 5; // Same as in calculateMarketStructure
	    
	    let workingData = [...data];
	    
	    let currentStructure = calculateMarketStructure(workingData);
	    if (!currentStructure) return [];
	    
	    structures.push(currentStructure);
	    
	    while (structures.length < count) {
	        const currentStartIndex = currentStructure.startIndex;
	        
	        if (currentStartIndex <= structureLen * 2) break;
	        
	        workingData = workingData.slice(0, currentStartIndex);
	        
	        const prevStructure = calculateMarketStructure(workingData);
	        if (!prevStructure) break;
	        
	        structures.push(prevStructure);
	        
	        currentStructure = prevStructure;
	    }
	    
	    structures.shift();
	    
	    return structures;
	}
	
	function calculateOverallFibonacciRetracement(data) {
	    if (data.length === 0) return null;
	    let highestHigh = -Infinity, lowestLow = Infinity;
	    let highestHighTime = null, lowestLowTime = null;
	
	    data.forEach(item => {
	        if (item.high > highestHigh) {
	            highestHigh = item.high;
	            highestHighTime = item.time;
	        }
	        if (item.low < lowestLow) {
	            lowestLow = item.low;
	            lowestLowTime = item.time;
	        }
	    });
	
	    if (highestHigh === -Infinity || lowestLow === Infinity) return null;
	
	    const diff = highestHigh - lowestLow;
	    // Fib 0.5 retracement is calculated from the highest high downwards to lowest low
	    const fib0_5 = highestHigh - (diff * 0.5);
	
	    return {
	        highestHigh: highestHigh,
	        highestHighTime: highestHighTime,
	        lowestLow: lowestLow,
	        lowestLowTime: lowestLowTime,
	        fib0_5_level: fib0_5,
	        levels: {
	            "1.000": highestHigh,
	            "0.786": highestHigh-(diff*0.786),
	            "0.618": highestHigh-(diff*0.618),
	            "0.500": fib0_5,
	            "0.382": highestHigh-(diff*0.382),
	            "0.236": highestHigh-(diff*0.236),
	            "0.000": lowestLow
	        }
	    };
	}
	
	function generateTradeAnalysisReport(symbol) {
	    let recommendation = "", tradeType = 'neutral', reasons = [], targets = [], stopLoss = null, stopLossReason = "";
	    if (!currentStockData || currentStockData.length === 0 || currentPrice === null || !currentMarketStructure || !currentOverallFib) {
	        return { recommendation: "Insufficient data for a definitive analysis based on requested criteria.", type: 'neutral', reasons: [], targets: [], stopLoss: null, stopLossReason: "" };
	    }
	
	    const currentClose = currentStockData[currentStockData.length - 1].close;
	    const msFib0_5 = currentMarketStructure.fib0_5_level;
	    const tolerance = 0.01; // 1% tolerance for consolidation detection
	
	    let trendDescription = "";
	    let triggerLevelText = "";
	
	    if (currentClose > msFib0_5 && (currentClose - msFib0_5) > (msFib0_5 * tolerance) ) { // Ensure a clear close above
	        tradeType = 'buy';
	        trendDescription = "Strong Bullish";
	        triggerLevelText = `Buy Trigger Level: ₹${msFib0_5.toFixed(2)}`;
	        stopLoss = currentMarketStructure.bottom.toFixed(2);
	        stopLossReason = `Place stop loss at ₹${currentMarketStructure.bottom.toFixed(2)}. If price drops below this level after entry, the bullish market structure may be invalidated.`;
	
	        let tempTargets = [];
	        for (const levelKey in currentOverallFib.levels) {
	            const levelValue = currentOverallFib.levels[levelKey];
	            if (levelValue > currentClose) {
	                tempTargets.push({ value: levelValue, label: `Overall Fib ${levelKey}` });
	            }
	        }
	        tempTargets.sort((a, b) => a.value - b.value); // Sort ascending (nearest to farthest for buy)
	        targets = tempTargets.map((t, index) => `T${index + 1}: ₹${t.value.toFixed(2)}`);
	
	    }
	    else if (currentClose < msFib0_5 && (msFib0_5 - currentClose) > (msFib0_5 * tolerance) ) { // Ensure a clear close below
	        tradeType = 'sell';
	        trendDescription = "Strong Bearish";
	        triggerLevelText = `Sell Trigger Level: ₹${msFib0_5.toFixed(2)}`;
	        stopLoss = currentMarketStructure.top.toFixed(2);
	        stopLossReason = `Place stop loss at ₹${currentMarketStructure.top.toFixed(2)}. If price rises above this level after entry, the bearish market structure may be invalidated.`;
	
	        let tempTargets = [];
	        for (const levelKey in currentOverallFib.levels) {
	            const levelValue = currentOverallFib.levels[levelKey];
	            if (levelValue < currentClose) {
	                tempTargets.push({ value: levelValue, label: `Overall Fib ${levelKey}` });
	            }
	        }
	        tempTargets.sort((a, b) => b.value - a.value); // Sort descending (nearest to farthest for sell)
	        targets = tempTargets.map((t, index) => `T${index + 1}: ₹${t.value.toFixed(2)}`);
	
	    } else { // Price is consolidating or unclear around MS Fib 0.5
	        tradeType = 'neutral';
	        trendDescription = "Neutral / Consolidating";
	        triggerLevelText = `Key Level: ₹${msFib0_5.toFixed(2)} (Market Structure Midpoint)`;
	        recommendation = `The stock is consolidating around a key level. Wait for a clear breakout above or breakdown below ₹${msFib0_5.toFixed(2)} before making a move.`;
	    }
	
	    let mainRecommendationText = "";
	    if (tradeType === 'buy') {
	        mainRecommendationText = "A strong buy signal has been triggered. The price has moved above key resistance.";
	    } else if (tradeType === 'sell') {
	        mainRecommendationText = "A strong sell signal has been triggered. The price has dropped below key support.";
	    } else {
	        mainRecommendationText = recommendation; // Use the neutral recommendation already set
	    }
	    let formattedRecommendation = `<strong>Trend:</strong> ${trendDescription}<br>`;
	    formattedRecommendation += `<strong>Current Price:</strong> ₹${currentPrice.toFixed(2)}<br>`;
	    formattedRecommendation += `<strong>${triggerLevelText}</strong><br>`;
	    if (stopLoss) {
	        formattedRecommendation += `<strong>Stop Loss:</strong> ₹${stopLoss}<br>`;
	    }
	    formattedRecommendation += `<br>${mainRecommendationText}`;
	
	    if (targets.length > 0) {
	        formattedRecommendation += `<br><br>🎯 <strong>Targets:</strong>`;
	        targets.forEach(target => {
	            formattedRecommendation += `<br>•⁠  ⁠${target}`;
	        });
	    }
	
	    return { recommendation: formattedRecommendation, type: tradeType, reasons, targets, stopLoss, stopLossReason };
	}
	
	async function analyzeStock(symbol) {
	    $('#loading').removeClass('hidden');
	    hideMessageBox('error-message');
	    $('#analysis-output').addClass('hidden'); // Initially hide while loading
	    $('#currentSymbolDisplay').text(symbol);
	
	    try {
	        const [dailyCandles, price] = await Promise.all([
	            fetchHistoricalCandles(symbol),
	            fetchCurrentPrice(symbol)
	        ]);
	
	        if (dailyCandles.length === 0) throw new Error("No historical daily data available.");
	
	        currentStockData = dailyCandles;
	        currentPrice = price;
	
	        const smaPeriod = 10;
	        const smaData = calculateSMA(currentStockData, smaPeriod);
	        currentSMA = { data: smaData, signals: detectSMASignals(currentStockData, smaData, smaPeriod) };
	        currentSwingPoints = findSwingHighLows(currentStockData); // Used for UI display and chart markers
	        currentMarketStructure = calculateMarketStructure(currentStockData); // Modified for small structures
	        previousMarketStructures = findPreviousMarketStructures(currentStockData, 10); // Find previous 10 market structures
	        currentOverallFib = calculateOverallFibonacciRetracement(currentStockData);
	
	        $('#currentPriceDisplay').text(currentPrice ? currentPrice.toFixed(2) : 'N/A');
	        $('#currentPriceDate').text(currentStockData.length > 0 ? `(Live)` : '');
	
	        const latestSmaSignal = currentSMA.signals.length > 0 ? currentSMA.signals[currentSMA.signals.length - 1] : null;
	        $('#latestSmaSignalDisplay').text(latestSmaSignal ? `${latestSmaSignal.type} @ ${latestSmaSignal.price.toFixed(2)}` : 'N/A');
	        $('#latestSmaSignalDate').text(latestSmaSignal ? `on ${latestSmaSignal.time}` : '');
	
	        $('#latestSwingHighDisplay').text(currentSwingPoints.latestHigh ? `${currentSwingPoints.latestHigh.price.toFixed(2)}` : 'N/A');
	        $('#latestSwingHighDate').text(currentSwingPoints.latestHigh ? `on ${currentSwingPoints.latestHigh.time}` : '');
	        $('#latestSwingLowDisplay').text(currentSwingPoints.latestLow ? `${currentSwingPoints.latestLow.price.toFixed(2)}` : 'N/A');
	        $('#latestSwingLowDate').text(currentSwingPoints.latestLow ? `on ${currentSwingPoints.latestLow.time}` : '');
	
	        if (currentMarketStructure) {
	            const { type, top, bottom, fib0_5_level, breakout, time } = currentMarketStructure;
	            const typeColor = type === 'bullish' ? 'text-green-600' : 'text-red-600';
	            const msHtml = `
	                <div class="text-sm text-right">
	                    <div class="text-left"><strong>Type:</strong> <span class="font-bold ${typeColor}">${type}</span></div>
	                    <div class="text-left"><strong>Range:</strong> ${bottom.toFixed(2)} - ${top.toFixed(2)}</div>
	                    <div class="font-bold text-base mt-1 text-right">${fib0_5_level.toFixed(2)} (${breakout})</div>
	                    <div class="text-xs text-gray-500 mt-1 text-right">based on structure identified near ${time}</div>
	                </div>`;
	            $('#msFibDetails').html(msHtml);
	        } else {
	            $('#msFibDetails').html('<div class="detail-value-container"><span class="detail-value">N/A</span></div>');
	        }
	
	        if (currentOverallFib) {
	            $('#overallFibDisplay').text(`${currentOverallFib.fib0_5_level.toFixed(2)}`);
	            let overallFibText = `(from ${currentOverallFib.lowestLow.toFixed(2)} on ${currentOverallFib.lowestLowTime} to ${currentOverallFib.highestHigh.toFixed(2)} on ${currentOverallFib.highestHighTime})`;
	            $('#overallFibDate').html(overallFibText);
	        } else {
	            $('#overallFibDisplay').text('N/A');
	            $('#overallFibDate').text('');
	        }
	
	        const tradeReport = generateTradeAnalysisReport(symbol);
	        const tradeRecommendationOutput = $('#tradeRecommendationOutput');
	        tradeRecommendationOutput.removeClass().addClass(`trade-recommendation ${tradeReport.type}`);
	        tradeRecommendationOutput.html(tradeReport.recommendation);
	
	
	        $('#analysis-output').removeClass('hidden');
	        await displayChartAndIndicators(symbol, currentStockData);
	
	    } catch (error) {
	        showMessageBox(`Error analyzing stock: ${error.message}`, 'error');
	        $('#analysis-output').addClass('hidden');
	    } finally {
	        $('#loading').addClass('hidden');
	    }
	}
	
	async function displayChartAndIndicators(symbol, chartData) {
	    if (chart) chart.remove(); // Dispose of the old chart
	    $('#chart').html(''); // Clear the div
	
	    overallFibonacciLines = [];
	    marketStructureFibonacciLines = [];
	    previousMarketStructureLines = [];
	    swingHighMarkers = [];
	    swingLowMarkers = [];
	    smaSignalMarkers = [];
	
	    chart = LightweightCharts.createChart(document.getElementById('chart'), {
	        layout: { background: { color: '#ffffff' }, textColor: '#333' },
	        grid: { vertLines: { color: '#eee' }, horzLines: { color: '#eee' }, },
	        timeScale: {
	            timeVisible: true,
	            secondsVisible: false,
	            rightOffset: 12,
	            barSpacing: 10
	        },
	        crosshair: { mode: 1 },
	        rightPriceScale: {
	            autoScale: true,
	        },
	        localization: {
	            priceFormatter: price => price.toFixed(2),
	            timeFormatter: time => new Date(time * 1000).toLocaleDateString()
	        }
	    });
	
	    candleSeries = chart.addCandlestickSeries({
	        upColor: '#4CAF50', // Green
	        downColor: '#EF5350', // Red
	        borderUpColor: '#4CAF50',
	        borderDownColor: '#EF5350',
	        wickUpColor: '#4CAF50',
	        wickDownColor: '#EF5350'
	    });
	    candleSeries.setData(chartData);
	
	    // 1. SMA (10-day)
	    const smaData = calculateSMA(chartData, 10);
	    smaSeries = chart.addLineSeries({ color: 'blue', lineWidth: 2, title: `10 SMA` });
	    smaSeries.setData(smaData);
	
	    // 2. SMA Signals as markers
	    const smaSignals = currentSMA.signals.map(signal => {
	        return {
	            time: signal.time,
	            position: signal.type === 'Buy' ? 'belowBar' : 'aboveBar',
	            color: signal.type === 'Buy' ? '#26A69A' : '#EF5350',
	            shape: 'arrowUp',
	            text: `${signal.type} Signal @ ${signal.price.toFixed(2)}`
	        };
	    });
	    candleSeries.setMarkers(smaSignals);
	    smaSignalMarkers = smaSignals; // Keep track for toggling
	
	    // 3. Overall Fib
	    const overallFibLevels = currentOverallFib;
	    if(overallFibLevels) {
	        const fibColors = ['#78909C', '#FFD54F', '#EF5350', '#AB47BC', '#FFA726', '#66BB6A', '#42A5F5']; // Grey, Yellow, Red, Purple, Orange, Green, Blue
	        Object.entries(overallFibLevels.levels).forEach(([levelKey, levelValue], i) => {
	            const fibLine = chart.addLineSeries({
	                color: fibColors[i % fibColors.length],
	                lineWidth: 1,
	                lineStyle: LightweightCharts.LineStyle.Dotted,
	                title: `Overall Fib ${levelKey}`
	            });
	            fibLine.setData(chartData.map(d => ({ time: d.time, value: levelValue })));
	            overallFibonacciLines.push(fibLine);
	        });
	    }
	
	    const msFib = currentMarketStructure;
	    if (msFib && chartData.length > 0) {
	        const msColor = msFib.type === 'bullish' ? 'rgba(8, 153, 129, 0.8)' : 'rgba(242, 54, 69, 0.8)'; // Green/Red with opacity
	
	        const startIndexForPlotting = msFib.startIndex;
	        const relevantData = chartData.slice(startIndexForPlotting);
	
	        const msTopSeries = chart.addLineSeries({ color: msColor, lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Solid, title: `MS ${msFib.type} Top` });
	        msTopSeries.setData(relevantData.map(d => ({ time: d.time, value: msFib.top })));
	        marketStructureFibonacciLines.push(msTopSeries);
	
	        const msBottomSeries = chart.addLineSeries({ color: msColor, lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Solid, title: `MS ${msFib.type} Bottom` });
	        msBottomSeries.setData(relevantData.map(d => ({ time: d.time, value: msFib.bottom })));
	        marketStructureFibonacciLines.push(msBottomSeries);
	
	        const msMidSeries = chart.addLineSeries({ color: msColor, lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dashed, title: `MS ${msFib.type} 0.5` });
	        msMidSeries.setData(relevantData.map(d => ({ time: d.time, value: msFib.allLevels['0.500'] })));
	        marketStructureFibonacciLines.push(msMidSeries);
	
	        for (const levelKey in msFib.allLevels) {
	            if (levelKey !== '0.000' && levelKey !== '0.500' && levelKey !== '1.000') {
	                const msLevelSeries = chart.addLineSeries({
	                    color: msColor.replace('0.8', '0.4'),
	                    lineWidth: 1,
	                    lineStyle: LightweightCharts.LineStyle.Dotted,
	                    title: `MS Fib ${levelKey}`
	                });
	                msLevelSeries.setData(relevantData.map(d => ({ time: d.time, value: msFib.allLevels[levelKey] })));
	                marketStructureFibonacciLines.push(msLevelSeries);
	            }
	        }
	    }
	
	    previousMarketStructures.forEach((ms, idx) => {
	        const opacity = 0.3 + (0.7 * (1 - (idx / previousMarketStructures.length))); // Fade older structures
	        const msColor = ms.type === 'bullish' ? 
	            `rgba(8, 153, 129, ${opacity})` : 
	            `rgba(242, 54, 69, ${opacity})`;
	        
	        const relevantData = chartData.slice(ms.startIndex, ms.endIndex + 1);
	        
	        if (relevantData.length > 0) {
	            const msTopSeries = chart.addLineSeries({ 
	                color: msColor, 
	                lineWidth: 1, 
	                lineStyle: LightweightCharts.LineStyle.Solid, 
	                title: `Previous MS ${idx+1} Top`,
	                visible: false // Initially hidden
	            });
	            msTopSeries.setData(relevantData.map(d => ({ time: d.time, value: ms.top })));
	            previousMarketStructureLines.push(msTopSeries);
	            
	            const msBottomSeries = chart.addLineSeries({ 
	                color: msColor, 
	                lineWidth: 1, 
	                lineStyle: LightweightCharts.LineStyle.Solid, 
	                title: `Previous MS ${idx+1} Bottom`,
	                visible: false
	            });
	            msBottomSeries.setData(relevantData.map(d => ({ time: d.time, value: ms.bottom })));
	            previousMarketStructureLines.push(msBottomSeries);
	            
	            // Plot 0.5 level
	            const msMidSeries = chart.addLineSeries({ 
	                color: msColor, 
	                lineWidth: 1, 
	                lineStyle: LightweightCharts.LineStyle.Dashed, 
	                title: `Previous MS ${idx+1} 0.5`,
	                visible: false
	            });
	            msMidSeries.setData(relevantData.map(d => ({ time: d.time, value: ms.allLevels['0.500'] })));
	            previousMarketStructureLines.push(msMidSeries);
	        }
	    });
	
	    currentSwingPoints.allHighs.forEach(sh => {
	        swingHighMarkers.push({
	            time: sh.time,
	            position: 'aboveBar',
	            color: '#FFD700',
	            shape: 'circle',
	            text: `Swing High: ${sh.price.toFixed(2)}`
	        });
	    });
	    currentSwingPoints.allLows.forEach(sl => {
	        swingLowMarkers.push({
	            time: sl.time,
	            position: 'belowBar',
	            color: '#A9A9A9',
	            shape: 'circle',
	            text: `Swing Low: ${sl.price.toFixed(2)}`
	        });
	    });
	    candleSeries.setMarkers([...smaSignals, ...swingHighMarkers, ...swingLowMarkers]);
	
	    chart.timeScale().fitContent();
	    updateTogglesVisibility();
	}
	
	function updateTogglesVisibility() {
	    $('#toggleSma').prop('checked', smaSeries && smaSeries.options().visible);
	    $('#toggleOverallFib').prop('checked', overallFibonacciLines.length > 0 && overallFibonacciLines[0].options().visible);
	    $('#toggleMarketStructureFib').prop('checked', marketStructureFibonacciLines.length > 0 && marketStructureFibonacciLines[0].options().visible);
	    $('#togglePreviousMSFib').prop('checked', previousMarketStructureLines.length > 0 && previousMarketStructureLines[0].options().visible);
	
	    const currentMarkers = [];
	    if ($('#toggleSmaSignals').prop('checked')) {
	        currentMarkers.push(...smaSignalMarkers);
	    }
	    if ($('#toggleSwingPoints').prop('checked')) {
	        currentMarkers.push(...swingHighMarkers, ...swingLowMarkers);
	    }
	    candleSeries.setMarkers(currentMarkers);
	}
	
	$('#toggleSma').on('change', function() { if (smaSeries) smaSeries.applyOptions({ visible: this.checked }); });
	$('#toggleOverallFib').on('change', function() { overallFibonacciLines.forEach(s => s.applyOptions({ visible: this.checked })); });
	$('#toggleMarketStructureFib').on('change', function() { marketStructureFibonacciLines.forEach(s => s.applyOptions({ visible: this.checked })); });
	$('#togglePreviousMSFib').on('change', function() { previousMarketStructureLines.forEach(s => s.applyOptions({ visible: this.checked })); });
	$('#toggleSwingPoints').on('change', function() {
	    updateTogglesVisibility();
	});
	$('#toggleSmaSignals').on('change', function() {
	    updateTogglesVisibility();
	});
	
	window.addEventListener('resize', () => {
	    if (chart) {
	        chart.resize(document.getElementById('chart-container').clientWidth, document.getElementById('chart-container').clientHeight);
	        chart.timeScale().fitContent();
	    }
	});
	
	$(document).ready(() => { loadSymbolsFromApi('NSE'); });
</script>
<script>
	document.addEventListener('DOMContentLoaded', () => {
	const hamburger = document.getElementById('hamburger-menu');
	const navDropdown = document.getElementById('nav-dropdown');
	
	hamburger.addEventListener('click', () => {
	navDropdown.classList.toggle('active');
	});
	
	document.addEventListener('click', (event) => {
	if (!navDropdown.contains(event.target) && !hamburger.contains(event.target)) {
	 navDropdown.classList.remove('active');
	}
	});
	
	const tabButtons = document.querySelectorAll('.tab-button');
	const tabContents = document.querySelectorAll('.tab-content');
	
	tabButtons.forEach(button => {
	button.addEventListener('click', () => {
	 const targetTab = button.dataset.tab;
	
	 tabButtons.forEach(btn => btn.classList.remove('active'));
	 tabContents.forEach(content => content.classList.remove('active'));
	
	 button.classList.add('active');
	 document.getElementById(targetTab).classList.add('active');
	});
	});
	
	if (tabButtons.length > 0) {
	tabButtons[0].click();
	}
	});
</script>
@endsection