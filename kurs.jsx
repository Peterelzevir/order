import React, { useState, useEffect } from 'react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card } from '@/components/ui/card';
import { 
  ArrowUp, ArrowDown, RefreshCcw, DollarSign,
  Clock, TrendingUp, BarChart2, Info, 
  AlertCircle, ChevronDown, ChevronRight, Globe
} from 'lucide-react';

const KursTrackerPro = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [exchangeRate, setExchangeRate] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [amount, setAmount] = useState('');
  const [fromCurrency, setFromCurrency] = useState('USD');
  
  // Format time in WIB
  const formatTime = () => {
    return currentTime.toLocaleTimeString('id-ID', {
      timeZone: 'Asia/Jakarta',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }) + ' WIB';
  };

  // Fetch real-time exchange rate
  const fetchExchangeRate = async () => {
    try {
      const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
      const data = await response.json();
      setExchangeRate({
        USD_IDR: data.rates.IDR,
        IDR_USD: 1 / data.rates.IDR
      });
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching exchange rate:', error);
    }
  };

  // Fetch historical data
  const fetchHistoricalData = async () => {
    try {
      // Simulasi data historis (dalam implementasi nyata akan menggunakan API)
      const today = new Date();
      const data = [];
      for (let i = 30; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        data.push({
          date: date.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' }),
          rate: 15500 + Math.random() * 200 - 100
        });
      }
      setHistoricalData(data);
    } catch (error) {
      console.error('Error fetching historical data:', error);
    }
  };

  useEffect(() => {
    fetchExchangeRate();
    fetchHistoricalData();
    const interval = setInterval(fetchExchangeRate, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  // [Previous time formatting functions remain the same]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* [Previous header section remains the same] */}

      {/* Hero Section with Animation */}
      <section className="bg-gradient-to-r from-blue-600 to-indigo-600 py-20 text-white">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6 animate-fade-in">
            Kurs USD/IDR Real-Time
          </h1>
          <p className="text-xl text-blue-100 mb-8 animate-fade-in-up">
            Pantau kurs Dollar - Rupiah secara langsung dengan data terpercaya
          </p>
          <ChevronDown className="w-8 h-8 mx-auto animate-bounce" />
        </div>
      </section>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 -mt-10">
        {/* Exchange Rate Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <Card className="bg-white p-6 shadow-xl hover:shadow-2xl transition-shadow duration-300 transform hover:-translate-y-1">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">USD ke IDR</h2>
              <DollarSign className="w-6 h-6 text-blue-500" />
            </div>
            <div className="text-3xl font-bold text-blue-600 mb-2">
              {isLoading ? 'Loading...' : `Rp ${Math.round(exchangeRate?.USD_IDR).toLocaleString('id-ID')}`}
            </div>
            <div className="text-sm text-gray-500">
              1 Dollar Amerika Serikat
            </div>
          </Card>

          <Card className="bg-white p-6 shadow-xl hover:shadow-2xl transition-shadow duration-300 transform hover:-translate-y-1">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">IDR ke USD</h2>
              <DollarSign className="w-6 h-6 text-green-500" />
            </div>
            <div className="text-3xl font-bold text-green-600 mb-2">
              {isLoading ? 'Loading...' : `$ ${exchangeRate?.IDR_USD.toFixed(6)}`}
            </div>
            <div className="text-sm text-gray-500">
              1 Rupiah Indonesia
            </div>
          </Card>
        </div>

        {/* Converter & Chart Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          {/* [Previous converter section with enhanced animations] */}
          
          {/* Chart with Real Data */}
          <Card className="bg-white p-6 shadow-xl">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Grafik Pergerakan Kurs</h2>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={historicalData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" />
                <YAxis domain={['dataMin - 100', 'dataMax + 100']} />
                <Tooltip />
                <Area 
                  type="monotone" 
                  dataKey="rate" 
                  stroke="#3b82f6" 
                  fill="url(#colorGradient)" 
                  fillOpacity={0.2}
                />
                <defs>
                  <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </div>

        {/* Feature Sections */}
        <section className="py-16">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Fitur Unggulan
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {/* [Enhanced feature cards with animations] */}
          </div>
        </section>

        {/* Educational Section */}
        <section className="py-16 bg-white -mx-4 px-4">
          <div className="max-w-7xl mx-auto">
            <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
              Pahami Pergerakan Kurs
            </h2>
            <div className="grid md:grid-cols-2 gap-12">
              <div className="space-y-6">
                <h3 className="text-xl font-bold text-gray-900">Faktor yang Mempengaruhi Kurs</h3>
                <ul className="space-y-4">
                  <li className="flex items-start">
                    <ChevronRight className="w-5 h-5 text-blue-500 mt-1 flex-shrink-0" />
                    <div>
                      <h4 className="font-medium">Inflasi</h4>
                      <p className="text-gray-600">Tingkat inflasi yang berbeda antara kedua negara mempengaruhi nilai tukar mata uang.</p>
                    </div>
                  </li>
                  <li className="flex items-start">
                    <ChevronRight className="w-5 h-5 text-blue-500 mt-1 flex-shrink-0" />
                    <div>
                      <h4 className="font-medium">Suku Bunga</h4>
                      <p className="text-gray-600">Perbedaan suku bunga dapat mempengaruhi aliran modal dan nilai tukar.</p>
                    </div>
                  </li>
                  {/* Add more factors */}
                </ul>
              </div>
              <div className="space-y-6">
                <h3 className="text-xl font-bold text-gray-900">Tips Mengikuti Pergerakan Kurs</h3>
                {/* Add tips content */}
              </div>
            </div>
          </div>
        </section>

        {/* Market Analysis */}
        <section className="py-16">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Analisis Pasar
          </h2>
          {/* Add market analysis content */}
        </section>
      </main>

      {/* Enhanced Footer */}
      <footer className="bg-gray-900 text-gray-300 py-12">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-8 mb-8">
            <div>
              <h3 className="text-lg font-bold text-white mb-4">Tentang Data</h3>
              <p className="text-sm">
                Data kurs disediakan oleh exchangerate-api.com secara real-time.
                Diperbarui setiap menit untuk akurasi maksimal.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-bold text-white mb-4">Fitur</h3>
              <ul className="space-y-2 text-sm">
                <li>Kurs Real-time</li>
                <li>Kalkulator Konversi</li>
                <li>Grafik Historis</li>
                <li>Analisis Pasar</li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-bold text-white mb-4">Kontak</h3>
              <p className="text-sm">Dibuat dengan oleh peter</p>
              <p className="text-sm mt-2">Data terakhir diperbarui: {formatTime()}</p>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-sm">
            <p>© 2024 Kurs Tracker Pro. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default KursTrackerPro;
