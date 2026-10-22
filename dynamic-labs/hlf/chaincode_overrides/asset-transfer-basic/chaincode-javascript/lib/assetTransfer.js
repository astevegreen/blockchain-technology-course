/*
 * Copyright IBM Corp. All Rights Reserved.
 *
 * SPDX-License-Identifier: Apache-2.0
 *
 * Diploma-native chaincode for the HLF student lab.
 *
 * Assets are stored with the generic field set (ID, Type, Level, Owner, Value)
 * so that the same contract serves both the diploma scenario and the trade
 * finance scenario used later in the lab. The positional argument order of
 * CreateAsset is preserved to match the tutorial narrative:
 *
 *   invoke create diploma-001 credential 4 "George Washington" 2024
 *   invoke create shipment-001 cargo     10 "Cascadia-Exporter" 50000
 *
 * CreateAsset also accepts two optional trailing args (fieldOfStudy,
 * degreeType) used by the diploma narrative to capture area of study
 * and degree type (e.g. "Computer Science", "Master of Science"). They
 * default to empty strings so existing 5-arg calls still work.
 */

'use strict';

const stringify = require('json-stringify-deterministic');
const sortKeysRecursive = require('sort-keys-recursive');
const { Contract } = require('fabric-contract-api');

// School ↔ MSP mapping generated at build time from schools.json.
// Falls back to consortium-only defaults if the file is missing
// (standalone dev without the build pipeline).
let _schoolMapping;
try {
    _schoolMapping = require('./schoolMapping.json');
} catch (_) {
    _schoolMapping = [
        { msp: 'Org1MSP', school: 'Cascadia State', prefixes: ['cascadia'] },
        { msp: 'Org2MSP', school: 'Chesapeake Canoe University', prefixes: ['chesapeake', 'canoe'] },
        { msp: 'Org3MSP', school: 'South Hudson Institute', prefixes: ['south hudson', 'southhudson'] },
        { msp: 'Org4MSP', school: 'Maple Leaf Academy', prefixes: ['maple leaf', 'mapleleaf'] },
    ];
}

class AssetTransfer extends Contract {

    _callerMspId(ctx) {
        return ctx.clientIdentity.getMSPID();
    }

    _schoolMspTable() {
        return _schoolMapping;
    }

    _schoolToMsp(displayName) {
        const key = (displayName || '').trim().toLowerCase();
        if (!key) return null;
        for (const row of this._schoolMspTable()) {
            for (const prefix of row.prefixes) {
                if (key.startsWith(prefix)) return row.msp;
            }
        }
        return null;
    }

    _mspToSchool(msp) {
        for (const row of this._schoolMspTable()) {
            if (row.msp === msp) return row.school;
        }
        return null;
    }

    async InitLedger(ctx) {
        const callerMsp = this._callerMspId(ctx);
        const assets = [
            {
                ID: 'diploma-sample-tubman',
                Type: 'credential',
                Level: 2,
                Owner: 'Harriet Tubman',
                Value: 2023,
                FieldOfStudy: 'Nursing',
                DegreeType: 'Bachelor of Science',
            },
            {
                ID: 'diploma-sample-franklin',
                Type: 'credential',
                Level: 4,
                Owner: 'Benjamin Franklin',
                Value: 2022,
                FieldOfStudy: 'Electrical Engineering',
                DegreeType: 'Master of Science',
            },
            {
                ID: 'diploma-sample-lincoln',
                Type: 'credential',
                Level: 4,
                Owner: 'Abraham Lincoln',
                Value: 2024,
                FieldOfStudy: 'Political Science',
                DegreeType: 'Master of Arts',
            },
            {
                ID: 'diploma-sample-lovelace',
                Type: 'credential',
                Level: 4,
                Owner: 'Ada Lovelace',
                Value: 2024,
                FieldOfStudy: 'Computer Science',
                DegreeType: 'Master of Science',
            },
        ];

        for (const asset of assets) {
            asset.docType = 'asset';
            asset.Status = 'active';
            asset.IssuerMSP = callerMsp;
            asset.Issuer = callerMsp;
            await this._saveAsset(ctx, asset);
            await ctx.stub.setEvent(
                'ASSET_CREATED',
                Buffer.from(stringify(sortKeysRecursive(asset)))
            );
        }
    }

    // CreateAsset: the issuing org is the caller. IssuerMSP is derived
    // from the signed creator identity and cannot be argument-spoofed.
    // The `issuer` arg is the human-readable school name; for credentials
    // we require it to match the caller's MSP so no school — consortium
    // or student peer — can forge a diploma as another. Non-credential
    // assets (cargo, shipments, etc.) skip this check.
    async CreateAsset(ctx, id, type, level, owner, value, fieldOfStudy, degreeType, issuer) {
        const exists = await this.AssetExists(ctx, id);
        if (exists) {
            throw new Error(`The asset ${id} already exists`);
        }

        const callerMsp = this._callerMspId(ctx);
        let resolvedIssuer = issuer || callerMsp;
        if (type === 'credential') {
            const callerSchool = this._mspToSchool(callerMsp);
            if (issuer && issuer.trim() !== '') {
                const claimedMsp = this._schoolToMsp(issuer);
                if (claimedMsp && claimedMsp !== callerMsp) {
                    throw new Error(
                        `Issuer forgery rejected: transaction signed by ${callerMsp} ` +
                        `(${callerSchool || 'unknown school'}) but the credential ` +
                        `claims to be issued by "${issuer}" (${claimedMsp}). ` +
                        `A school can only issue diplomas under its own MSP.`
                    );
                }
                // Claimed issuer matches caller's org, or is a freeform
                // string that doesn't resolve to any known school — in
                // the latter case IssuerMSP still records the truth.
                resolvedIssuer = issuer;
            } else if (callerSchool) {
                resolvedIssuer = callerSchool;
            }
        }

        const asset = {
            ID: id,
            Type: type,
            Level: Number(level),
            Owner: owner,
            Value: Number(value),
            FieldOfStudy: fieldOfStudy || '',
            DegreeType: degreeType || '',
            Status: 'active',
            IssuerMSP: callerMsp,
            Issuer: resolvedIssuer,
            docType: 'asset',
        };
        await this._saveAsset(ctx, asset);
        await ctx.stub.setEvent(
            'ASSET_CREATED',
            Buffer.from(stringify(sortKeysRecursive(asset)))
        );
        return JSON.stringify(asset);
    }

    async ReadAsset(ctx, id) {
        const asset = await this._readAssetObject(ctx, id);
        return JSON.stringify(asset);
    }

    // Only the original issuing org may modify a diploma. This prevents
    // one school from editing another school's credential, even if both
    // are endorsing members of the channel.
    async UpdateAsset(ctx, id, type, level, owner, value, fieldOfStudy, degreeType) {
        const asset = await this._readAssetObject(ctx, id);
        this._assertCallerIsIssuer(ctx, asset);
        asset.Type = type;
        asset.Level = Number(level);
        asset.Owner = owner;
        asset.Value = Number(value);
        if (fieldOfStudy !== undefined) asset.FieldOfStudy = fieldOfStudy;
        if (degreeType !== undefined) asset.DegreeType = degreeType;
        await this._saveAsset(ctx, asset);
        return JSON.stringify(asset);
    }

    _assertCallerIsIssuer(ctx, asset) {
        const callerMsp = this._callerMspId(ctx);
        // Legacy assets written before IssuerMSP existed have no lock;
        // this is only relevant during the Phase 6 → Phase 7 transition
        // and will go away once the ledger is regenerated from genesis.
        if (!asset.IssuerMSP) {
            return;
        }
        if (asset.IssuerMSP !== callerMsp) {
            throw new Error(
                `Issuer mismatch: asset ${asset.ID} was issued by ${asset.IssuerMSP}, ` +
                `but this transaction is signed by ${callerMsp}. ` +
                `Only the issuing org can modify or transfer its own credentials.`
            );
        }
    }

    // Same rule as UpdateAsset and TransferAsset: only the issuing org may remove
    // its own credential. _readAssetObject still throws "does not exist" for a missing id.
    async DeleteAsset(ctx, id) {
        const asset = await this._readAssetObject(ctx, id);
        this._assertCallerIsIssuer(ctx, asset);
        await ctx.stub.deleteState(id);
        await ctx.stub.setEvent(
            'REMOVED',
            Buffer.from(stringify(sortKeysRecursive({ ID: id })))
        );
        return true;
    }

    async AssetExists(ctx, id) {
        const assetJSON = await ctx.stub.getState(id);
        return assetJSON && assetJSON.length > 0;
    }

    async TransferAsset(ctx, id, newOwner) {
        const asset = await this._readAssetObject(ctx, id);
        this._assertCallerIsIssuer(ctx, asset);
        const oldOwner = asset.Owner;
        asset.Owner = newOwner;
        await this._saveAsset(ctx, asset);
        await ctx.stub.setEvent('TRANSFERRED', Buffer.from(stringify(sortKeysRecursive({
            ID: id,
            From: oldOwner,
            To: newOwner,
        }))));
        return oldOwner;
    }

    async GetAllAssets(ctx) {
        const allResults = [];
        const iterator = await ctx.stub.getStateByRange('', '');
        let result = await iterator.next();
        while (!result.done) {
            const strValue = Buffer.from(result.value.value.toString()).toString('utf8');
            let record;
            try {
                record = JSON.parse(strValue);
            } catch (err) {
                record = strValue;
            }
            allResults.push(record);
            result = await iterator.next();
        }
        return JSON.stringify(allResults);
    }

    // ------------------------------------------------------------------
    // Vehicle scenario — Westview Used-Car Exchange (Chapter 6)
    // ------------------------------------------------------------------

    // Westview consortium role mapping:
    //   Org1MSP → Westview DMV (title authority)
    //   Org2MSP → Garden State Insurance (claims, total losses)
    //   Org3MSP → Turnpike Inspection Authority (safety, emissions)
    //   Org4MSP → AutoFax (vehicle history aggregator)
    //   Student peers → independent dealerships / service centers

    _WESTVIEW_ROLES() {
        return {
            Org1MSP: 'Westview DMV',
            Org2MSP: 'Garden State Insurance',
            Org3MSP: 'Turnpike Inspection Authority',
            Org4MSP: 'AutoFax',
        };
    }

    _assertCallerRole(ctx, requiredMsp, roleName) {
        const callerMsp = this._callerMspId(ctx);
        if (callerMsp !== requiredMsp) {
            const callerLabel = this._WESTVIEW_ROLES()[callerMsp]
                || this._mspToSchool(callerMsp) || callerMsp;
            throw new Error(
                `Role violation: ${roleName} operations require ${requiredMsp}, ` +
                `but this transaction is signed by ${callerMsp} (${callerLabel}). ` +
                `Only the designated ${roleName} can perform this action.`
            );
        }
    }

    async SeedWestviewInventory(ctx) {
        const callerMsp = this._callerMspId(ctx);
        const cars = [
            { ID: 'car101', VIN: 'WV-F4K3-101-LE', Year: 2017, Make: 'Toyoda', Model: 'Coroll-Yeah', Color: 'silver', Mileage: 62000, Value: 12495, Owner: 'Westview DMV Impound' },
            { ID: 'car102', VIN: 'WV-F4K3-102-EX', Year: 2015, Make: 'Hondé', Model: 'Civ-ish', Color: 'red', Mileage: 88000, Value: 10995, Owner: 'Garden State Insurance Salvage' },
            { ID: 'car103', VIN: 'WV-F4K3-103-PR', Year: 2018, Make: 'SubaRoo', Model: 'Outbackpack', Color: 'green', Mileage: 54000, Value: 17995, Owner: 'Westview DMV Impound' },
            { ID: 'car104', VIN: 'WV-F4K3-104-SE', Year: 2014, Make: 'Fjord', Model: 'Escapé', Color: 'gray', Mileage: 97000, Value: 9995, Owner: 'Garden State Insurance Salvage' },
            { ID: 'car105', VIN: 'WV-F4K3-105-S', Year: 2019, Make: 'Voltswagon', Model: 'Jettison', Color: 'white', Mileage: 31000, Value: 18995, Owner: 'Westview DMV Impound' },
            { ID: 'car106', VIN: 'WV-F4K3-106-SV', Year: 2016, Make: 'Nissand', Model: 'Altimaybe', Color: 'black', Mileage: 76000, Value: 12995, Owner: 'Garden State Insurance Salvage' },
            { ID: 'car107', VIN: 'WV-F4K3-107-TR', Year: 2020, Make: 'Maz-Duh', Model: 'CX-Five-ish', Color: 'blue', Mileage: 24000, Value: 21995, Owner: 'Westview DMV Impound' },
            { ID: 'car108', VIN: 'WV-F4K3-108-LT', Year: 2013, Make: 'Chevrolate', Model: 'Malibruh', Color: 'gold', Mileage: 133000, Value: 8495, Owner: 'Garden State Insurance Salvage' },
            { ID: 'car109', VIN: 'WV-F4K3-109-LX', Year: 2020, Make: 'Kia-ya', Model: 'CR-Vroom', Color: 'tan', Mileage: 31000, Value: 18995, Owner: 'Westview DMV Impound' },
            { ID: 'car110', VIN: 'WV-F4K3-110-SP', Year: 2013, Make: 'Jëëp', Model: 'Patri-not', Color: 'navy', Mileage: 101000, Value: 10495, Owner: 'Garden State Insurance Salvage' },
        ];
        for (const car of cars) {
            car.Type = 'vehicle';
            car.docType = 'asset';
            car.ListedByMSP = callerMsp;
            car.TitleStatus = 'clean';
            car.InspectionStatus = 'passed';
            car.InsuranceClaims = [];
            car.ServiceHistory = [];
            car.Flags = [];
            await this._saveAsset(ctx, car);
            await ctx.stub.setEvent(
                'VEHICLE_LISTED',
                Buffer.from(stringify(sortKeysRecursive({ ID: car.ID, VIN: car.VIN })))
            );
        }
    }

    async CreateVehicle(ctx, id, vin, year, make, model, color, mileage, value) {
        const exists = await this.AssetExists(ctx, id);
        if (exists) {
            throw new Error(`The asset ${id} already exists`);
        }
        const callerMsp = this._callerMspId(ctx);
        const callerSchool = this._mspToSchool(callerMsp);
        const asset = {
            ID: id,
            Type: 'vehicle',
            VIN: vin || '',
            Year: Number(year),
            Make: make || '',
            Model: model || '',
            Color: color || '',
            Mileage: Number(mileage),
            Value: Number(value),
            Owner: callerSchool || callerMsp,
            ListedByMSP: callerMsp,
            TitleStatus: 'pending',
            InspectionStatus: 'pending',
            InsuranceClaims: [],
            ServiceHistory: [],
            Flags: [],
            docType: 'asset',
        };
        await this._saveAsset(ctx, asset);
        await ctx.stub.setEvent(
            'VEHICLE_LISTED',
            Buffer.from(stringify(sortKeysRecursive({ ID: id, VIN: vin, ListedByMSP: callerMsp })))
        );
        return JSON.stringify(asset);
    }

    async AddServiceRecord(ctx, vehicleId, serviceCode, description) {
        const asset = await this._readAssetObject(ctx, vehicleId);
        if (asset.Type !== 'vehicle') {
            throw new Error(`Asset ${vehicleId} is not a vehicle`);
        }
        const callerMsp = this._callerMspId(ctx);
        const callerLabel = this._mspToSchool(callerMsp)
            || this._WESTVIEW_ROLES()[callerMsp] || callerMsp;
        const record = {
            serviceCode: serviceCode || '',
            description: description || '',
            providerMSP: callerMsp,
            provider: callerLabel,
            timestamp: ctx.stub.getTxTimestamp().seconds.low,
            txId: ctx.stub.getTxID(),
        };
        if (!Array.isArray(asset.ServiceHistory)) asset.ServiceHistory = [];
        asset.ServiceHistory.push(record);
        await this._saveAsset(ctx, asset);
        await ctx.stub.setEvent(
            'SERVICE_RECORDED',
            Buffer.from(stringify(sortKeysRecursive({ ID: vehicleId, serviceCode, providerMSP: callerMsp })))
        );
        return JSON.stringify(asset);
    }

    async SetTitleStatus(ctx, vehicleId, status, detail) {
        this._assertCallerRole(ctx, 'Org1MSP', 'Westview DMV');
        const asset = await this._readAssetObject(ctx, vehicleId);
        if (asset.Type !== 'vehicle') {
            throw new Error(`Asset ${vehicleId} is not a vehicle`);
        }
        asset.TitleStatus = status || 'clean';
        if (!Array.isArray(asset.ServiceHistory)) asset.ServiceHistory = [];
        asset.ServiceHistory.push({
            serviceCode: 'title-update',
            description: `Title set to ${status}${detail ? ': ' + detail : ''}`,
            providerMSP: 'Org1MSP',
            provider: 'Westview DMV',
            timestamp: ctx.stub.getTxTimestamp().seconds.low,
            txId: ctx.stub.getTxID(),
        });
        await this._saveAsset(ctx, asset);
        await ctx.stub.setEvent(
            'TITLE_UPDATED',
            Buffer.from(stringify(sortKeysRecursive({ ID: vehicleId, TitleStatus: status })))
        );
        return JSON.stringify(asset);
    }

    async ReportInsuranceClaim(ctx, vehicleId, claimType, detail) {
        this._assertCallerRole(ctx, 'Org2MSP', 'Garden State Insurance');
        const asset = await this._readAssetObject(ctx, vehicleId);
        if (asset.Type !== 'vehicle') {
            throw new Error(`Asset ${vehicleId} is not a vehicle`);
        }
        const claim = {
            claimType: claimType || '',
            detail: detail || '',
            reportedByMSP: 'Org2MSP',
            timestamp: ctx.stub.getTxTimestamp().seconds.low,
            txId: ctx.stub.getTxID(),
        };
        if (!Array.isArray(asset.InsuranceClaims)) asset.InsuranceClaims = [];
        asset.InsuranceClaims.push(claim);
        await this._saveAsset(ctx, asset);
        await ctx.stub.setEvent(
            'INSURANCE_REPORTED',
            Buffer.from(stringify(sortKeysRecursive({ ID: vehicleId, claimType })))
        );
        return JSON.stringify(asset);
    }

    async SetInspectionResult(ctx, vehicleId, result, detail) {
        this._assertCallerRole(ctx, 'Org3MSP', 'Turnpike Inspection Authority');
        const asset = await this._readAssetObject(ctx, vehicleId);
        if (asset.Type !== 'vehicle') {
            throw new Error(`Asset ${vehicleId} is not a vehicle`);
        }
        asset.InspectionStatus = result || 'pending';
        if (!Array.isArray(asset.ServiceHistory)) asset.ServiceHistory = [];
        asset.ServiceHistory.push({
            serviceCode: 'inspection',
            description: `Inspection: ${result}${detail ? ' — ' + detail : ''}`,
            providerMSP: 'Org3MSP',
            provider: 'Turnpike Inspection Authority',
            timestamp: ctx.stub.getTxTimestamp().seconds.low,
            txId: ctx.stub.getTxID(),
        });
        await this._saveAsset(ctx, asset);
        await ctx.stub.setEvent(
            'INSPECTION_UPDATED',
            Buffer.from(stringify(sortKeysRecursive({ ID: vehicleId, InspectionStatus: result })))
        );
        return JSON.stringify(asset);
    }

    async FlagDiscrepancy(ctx, vehicleId, flag, detail) {
        this._assertCallerRole(ctx, 'Org4MSP', 'AutoFax');
        const asset = await this._readAssetObject(ctx, vehicleId);
        if (asset.Type !== 'vehicle') {
            throw new Error(`Asset ${vehicleId} is not a vehicle`);
        }
        const entry = {
            flag: flag || '',
            detail: detail || '',
            flaggedByMSP: 'Org4MSP',
            timestamp: ctx.stub.getTxTimestamp().seconds.low,
            txId: ctx.stub.getTxID(),
        };
        if (!Array.isArray(asset.Flags)) asset.Flags = [];
        asset.Flags.push(entry);
        await this._saveAsset(ctx, asset);
        await ctx.stub.setEvent(
            'DISCREPANCY_FLAGGED',
            Buffer.from(stringify(sortKeysRecursive({ ID: vehicleId, flag })))
        );
        return JSON.stringify(asset);
    }

    async TransferVehicle(ctx, vehicleId, newOwner) {
        const asset = await this._readAssetObject(ctx, vehicleId);
        if (asset.Type !== 'vehicle') {
            throw new Error(`Asset ${vehicleId} is not a vehicle`);
        }
        const callerMsp = this._callerMspId(ctx);
        if (asset.ListedByMSP && asset.ListedByMSP !== callerMsp) {
            throw new Error(
                `Transfer denied: vehicle ${vehicleId} was listed by ${asset.ListedByMSP}, ` +
                `but this transaction is signed by ${callerMsp}. ` +
                `Only the listing org can transfer a vehicle.`
            );
        }
        const oldOwner = asset.Owner;
        asset.Owner = newOwner;
        asset.ListedByMSP = callerMsp;
        if (!Array.isArray(asset.ServiceHistory)) asset.ServiceHistory = [];
        asset.ServiceHistory.push({
            serviceCode: 'transfer',
            description: `Ownership transferred from ${oldOwner} to ${newOwner}`,
            providerMSP: callerMsp,
            provider: this._mspToSchool(callerMsp) || callerMsp,
            timestamp: ctx.stub.getTxTimestamp().seconds.low,
            txId: ctx.stub.getTxID(),
        });
        await this._saveAsset(ctx, asset);
        await ctx.stub.setEvent('VEHICLE_TRANSFERRED', Buffer.from(stringify(sortKeysRecursive({
            ID: vehicleId,
            From: oldOwner,
            To: newOwner,
        }))));
        return oldOwner;
    }

    // ------------------------------------------------------------------
    // internal helpers
    // ------------------------------------------------------------------

    async _readAssetObject(ctx, id) {
        const assetJSON = await ctx.stub.getState(id);
        if (!assetJSON || assetJSON.length === 0) {
            throw new Error(`The asset ${id} does not exist`);
        }
        return JSON.parse(assetJSON.toString());
    }

    async _saveAsset(ctx, asset) {
        await ctx.stub.putState(
            asset.ID,
            Buffer.from(stringify(sortKeysRecursive(asset)))
        );
    }
}

module.exports = AssetTransfer;
